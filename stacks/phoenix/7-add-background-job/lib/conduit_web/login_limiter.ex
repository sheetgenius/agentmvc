defmodule ConduitWeb.LoginLimiter do
  use Hammer, backend: :ets
end
