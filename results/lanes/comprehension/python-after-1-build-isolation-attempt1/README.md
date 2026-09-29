# Failed reader preparation probe

This dummy-file probe found that inheriting the writable workspace profile still allowed source writes. Parent reads were denied. No comprehension reader was launched and no application source was exposed to this probe. The preparation was preserved, the profile was changed to inherit read-only access, and a fresh probe passed before the actual reader ran. This is harness preparation evidence, excluded from reader effort.
