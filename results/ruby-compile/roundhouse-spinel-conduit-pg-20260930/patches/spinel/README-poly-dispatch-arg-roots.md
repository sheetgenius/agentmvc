# c01: Spinel GC lifetime bug: unrooted temps in poly-dispatch calls

Spinel 813def1fb (matz/spinel). This worker delivers a deterministic standalone
repro, the root cause, a two-hunk codegen fix with a regression test in
Spinel's own style, and the verification.

## Problem

The Roundhouse/Conduit server compiled by Spinel runs this in `ArticlesController#create`:

```ruby
article = Article.new(permitted(input, %i[title description body]).merge(
  author: @current_user, status: status,
  published_at: (Time.now.utc if status == "published"),
  tag_list: tags.uniq, slug: Article.slug_for(input["title"])))
```

Under load it died with SIGSEGV in `sp_str_length` <- `sp_Db_s_encode_array`
(the `each_char` over `tag_list`). With the tags copied first, the crash went
away, but `published_at` sometimes came back as year 8920956. Both symptoms
appeared with `SPINEL_WORKERS=1` too.

## Root cause

`permitted(...)` returns `untyped`, so `.merge(...)` is a **boxed-receiver
(poly) dispatch**. The codegen evaluates every argument into a C temp before
it chooses the arm for the runtime class. **Only the receiver temp is rooted.**
The positional and keyword argument temps are not:

- `src/codegen_call.c:8645-8647` (`emit_poly_method_dispatch`, starting at
  7184): the receiver temp gets `SP_GC_ROOT_RBVAL`.
- `src/codegen_call.c:8648-8672`: each positional argument temp
  (`sp_RbVal _tN = ...;` or `<ctype> _tN = ...;`) is declared with no root.
  The only exception is a splat.
- `src/codegen_call.c:8686-8704`: each keyword-value temp (`kwtmp[e]`) is
  also declared with no root.

A second gap sits one layer out. The operand `(Time.now.utc if cond)` is a
no-else `if`. It is lowered to a result temp declared in `g_pre`, ahead of the
whole statement, and that temp is not rooted either:

- `src/codegen_expr.c:3567-3578`: `emit_ctype(...); " _tN = default;"` with no
  root. The case-expression temp at `src/codegen_expr.c:1431` does root its temp,
  so the `if` temp is the one that doesn't.

The generated C for the app (`app-blog.c` in this directory, produced with
`spinel bin/blog.rb --rbs .` on a copy of `lead/runs/v2-e/out`):

```c
sp_RbVal _t6482 = sp_box_nil();
if (status == "published") _t6482 = sp_box_time(sp_time_utc(sp_time_now()));   // heap box, unrooted
...
_gcf.v[6] = ({ _gcf.v[7] = sp_ApplicationController_permitted(...);   // allocates
  sp_User * _t6479 = self->iv_current_user; sp_RbVal _t6480 = lv_status;
  sp_RbVal _t6481 = (_t6482);
  sp_PolyArray * _t6484 = sp_poly_uniq(lv_tags);            // fresh array, unrooted
  const char * _t6485 = sp_Article_s_slug_for(_gcf.v[5]);   // allocates -> may collect _t6484 / the Time box
  sp_pd_53(_gcf.v[7], _t6479, _t6480, _t6481, _t6484, _t6485); });
```

Inside `sp_pd_53`, the dispatch hoisted out of line by `pd_hoist`, each arm
runs `sp_SymPolyHash_new()` (`lib/spinel_rt.h:6982`, `sp_gc_alloc`). That can
trigger a collection too, before the arm stores the parameters into the hash.

A collection anywhere in that window frees:

- **the `tags.uniq` PolyArray** (`sp_poly_uniq`, `lib/spinel_rt.h:13264`). Its
  pool slot is reused by another array, so the merged hash holds a stale
  pointer. `Article#tag_list=` (RBS `Array[String]`) then copies element
  pointers out of it with `sp_poly_as_str_array` (`lib/spinel_rt.h:8310`).
  `encode_array` walks those strings and faults in `sp_str_length`. This is
  symptom 1.
- **the boxed Time** (`sp_box_time`, `lib/sp_cold.c:3587`, a 16-byte object
  with no scan). The slot is reused and `format_db_time` reads another
  object's bytes as `tv_sec`/`tv_nsec`: year 8920956. This is symptom 2. It
  comes from the `if` temp and survives the tags copy, which only changed the
  array.

Assigning each attribute through its typed writer (symptom 3) avoided both
because it never goes through a poly dispatch with fresh-value arguments.

It is not a threading bug. The collector is precise, so a value held only in
an unregistered C local is garbage. The threaded server only raises the
allocation rate that makes a collection land in the window. The standalone
repro faults single-threaded, with no stress flags.

## Fix

The patch is `patch/spinel-poly-dispatch-arg-roots.patch`, a `git diff`
against 813def1fb: 23 lines of codegen plus the test.

1. `src/codegen_call.c` (`emit_poly_method_dispatch`): after each positional
   argument temp and each keyword-value temp, emit
   `emit_gc_root_tmp(c, type, tmp, b)`. That helper is the existing type-aware
   root: `SP_GC_ROOT_RBVAL` for a boxed value, `SP_GC_ROOT_STR` for a String,
   `SP_GC_ROOT` for heap pointers, and nothing for a value type or scalar. The
   roots live in the call's statement expression, exactly like the receiver
   root beside them, and they cover the out-of-line `sp_pd_N` too, because
   the caller's rooted temps hold the same objects.
2. `src/codegen_expr.c` (no-else / multi-statement `if` as an expression): root
   the `g_pre` result temp when its type is rootable, the same way the
   case-expression temp at line 1431 already does.

Regression test: `test/poly_dispatch_arg_gc_root.rb` plus `.rb.expected`
(CRuby output). The receiver and the last argument call `GC.start`, then
allocate to reuse the freed slots. It covers the `if`-temp Time, a
keyword-argument `uniq` array, and a positional argument through a user method
on a boxed receiver.

## Verification

All runs use `spinel-spike-w01-toolchain:latest`. "Stock" is the image's
`spinel`. "Patched" is `/w/spinel/spinel`, built from `spinel/` in this
directory with `make -j8 CC=clang`.

| check | stock 813def1fb | patched |
|---|---|---|
| `repro/final/tag_time_merge.rb` (`--rbs .`), 300 iters, no env | **SIGSEGV (rc 139), 3/3 runs** | `done bad=0` |
| same, `SPINEL_GC_STRESS=1` | `done bad=316` (garbage tags, `Time(8374778257789187127)`) | `done bad=0` |
| `repro/final/threaded_long.rb`, 8 threads x 2000, `SPINEL_WORKERS=4` | **SIGSEGV (rc 139)** | `bad=0` |
| same, `SPINEL_WORKERS=1` | **SIGSEGV (rc 139)** | `bad=0` |
| `test/poly_dispatch_arg_gc_root.rb` vs CRuby | FAIL (Time reads 0/1, tags read `J1,K1,L1`) | PASS, 3/3, and under `SPINEL_GC_STRESS=1` |
| ablation: only the codegen_call.c hunk | - | tags fixed, **Time still wrong** in both the repro and the test, so hunk 2 is needed |
| long run, threaded 16x20000, `SPINEL_WORKERS=8` / `=1` | - | `bad=0` / `bad=0` (320k iterations each) |
| long run, threaded 8x1000, `SPINEL_WORKERS=4 SPINEL_GC_STRESS=1` | - | `bad=0` |
| long run, single-threaded 200000 iterations, and 20000 under `SPINEL_GC_STRESS=1` | - | `bad=0` |
| `make test-corpus -j8` (test/*.rb plus package tests) | the same 2 tests fail on stock | **4881 pass, 2 fail, 0 error** |

The 2 corpus failures are `io_select_set_parks_thread`, which times out, and
`pkg.tmpdir.tmpdir_expand_usable`, which prints `false/true/false` when run
as root in the container. Both fail the same way with the stock image
compiler, so they are environmental and unrelated to this patch. Logs:
`logs/test-corpus-patched.log`, `logs/long-run-patched.log`, `logs/run-sh.log`.

Commands:

```sh
# C = the investigation's scratch directory (not published): spinel/ is a Spinel 813def1fb checkout with this
# patch applied, repro/final/ holds the files in repro-poly-dispatch/, scratch/cmp.sh compares against CRuby.
C=/path/to/c01-spinel-lifetime
# build the patched compiler
docker run --rm --name spinel-spike-c01-build --cpus 8 -v $C:/w -w /w/spinel \
  spinel-spike-w01-toolchain:latest make -j8 CC=clang
# repro, stock vs patched
docker run --rm --name spinel-spike-c01-x --cpus 8 -v $C:/w -w /w/repro/final \
  spinel-spike-w01-toolchain:latest sh run.sh
# regression test, stock vs patched vs CRuby
docker run --rm --name spinel-spike-c01-t --cpus 8 -v $C:/w -w /w/spinel/test \
  spinel-spike-w01-toolchain:latest sh /w/scratch/cmp.sh poly_dispatch_arg_gc_root
```

In the app, regenerating its C with the patched compiler (`app-blog-patched.c`)
roots the create site:
`... sp_PolyArray * _t6484 = sp_poly_uniq(lv_tags); SP_GC_ROOT(_t6484); const char * _t6485 = ...; SP_GC_ROOT_STR(_t6485); ...`,
and the Time moves into a frame slot. Across the whole app the patch adds
about 165 per-root macros and 97 frame slots, so many other poly-dispatch
sites in the app had the same latent gap.

## Rule for app code until the patch lands

Do not pass a freshly allocated value (such as `x.uniq`, `Time.now`, `a.map{}`,
an `(expr if cond)`, or a string built inline) as an argument, positional or
keyword, to a method called on an **untyped/boxed receiver**, which is any
receiver whose type Spinel cannot pin (`permitted(...)`, `JSON.parse(...)[k]`,
`attrs[:x]`). Bind the receiver to a typed local first, or bind each fresh
value to a local variable before the call. Locals are rooted. Alternatively,
assign attributes through typed writers, as symptom 3 shows.

## Files

- `patch/spinel-poly-dispatch-arg-roots.patch`: the fix plus regression test (git diff vs 813def1fb)
- `spinel/`: patched Spinel checkout (813def1fb plus the patch), with vendored prism and rbs
- `repro/final/tag_time_merge.rb` + `.rbs`: minimal deterministic repro (JSON tags, Time, poly merge into an RBS-typed class)
- `repro/final/threaded_long.rb` + `.rbs`: threaded long-run variant
- `repro/final/run.sh`: stock-vs-patched driver
- `app/`, `app-blog.c`, `app-blog-patched.c`: copy of the emitted Conduit tree and its generated C before and after
- `logs/`: build and test-corpus logs
