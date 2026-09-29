defmodule Conduit.Accounts.LoginLimiterTest do
  use ExUnit.Case, async: false

  alias Conduit.Accounts.LoginLimiter

  test "a concurrent burst admits only 20 attempts, including reservations in flight" do
    email = "burst-#{System.unique_integer([:positive])}@test.com"
    parent = self()

    tasks =
      for _ <- 1..25 do
        Task.async(fn ->
          result = LoginLimiter.reserve(email)
          send(parent, {:reserved, self(), result})

          receive do
            :finish ->
              case result do
                {:ok, reservation} -> LoginLimiter.finish(reservation, :failed)
                :rate_limited -> :ok
              end
          end
        end)
      end

    replies =
      for _ <- 1..25 do
        assert_receive {:reserved, pid, result}, 5_000
        {pid, result}
      end

    assert Enum.count(replies, fn {_pid, result} -> match?({:ok, _}, result) end) == 20
    assert Enum.count(replies, fn {_pid, result} -> result == :rate_limited end) == 5

    {:ok, other_reservation} = LoginLimiter.reserve("other-#{email}")
    assert LoginLimiter.finish(other_reservation, :failed) == :ok

    Enum.each(replies, fn {pid, _result} -> send(pid, :finish) end)
    Enum.each(tasks, &Task.await(&1, 5_000))

    assert LoginLimiter.reserve(email) == :rate_limited
  end

  test "a successful login clears prior failures" do
    email = "cleared-#{System.unique_integer([:positive])}@test.com"

    for _ <- 1..19 do
      {:ok, reservation} = LoginLimiter.reserve(email)
      assert LoginLimiter.finish(reservation, :failed) == :ok
    end

    {:ok, reservation} = LoginLimiter.reserve(email)
    assert LoginLimiter.finish(reservation, :success) == :ok

    for _ <- 1..20 do
      {:ok, reservation} = LoginLimiter.reserve(email)
      assert LoginLimiter.finish(reservation, :failed) == :ok
    end

    assert LoginLimiter.reserve(email) == :rate_limited
  end

  test "a rescued verification error releases the reservation while its caller stays alive" do
    email = "rescued-#{System.unique_integer([:positive])}@test.com"
    parent = self()

    task =
      Task.async(fn ->
        rescued? =
          try do
            LoginLimiter.with_reservation(email, fn _reservation ->
              raise "verification failed"
            end)

            false
          rescue
            RuntimeError -> true
          end

        send(parent, {:rescued, self(), rescued?})

        receive do
          :stop -> :ok
        end
      end)

    assert_receive {:rescued, caller, true}, 5_000
    assert Process.alive?(caller)

    reservations =
      for _ <- 1..20 do
        {:ok, reservation} = LoginLimiter.reserve(email)
        reservation
      end

    assert LoginLimiter.reserve(email) == :rate_limited
    Enum.each(reservations, &LoginLimiter.cancel/1)
    send(caller, :stop)
    assert Task.await(task, 5_000) == :ok
  end

  test "a dead caller releases an unfinished reservation" do
    email = "dead-#{System.unique_integer([:positive])}@test.com"

    reservations =
      for _ <- 1..19 do
        {:ok, reservation} = LoginLimiter.reserve(email)
        reservation
      end

    parent = self()

    caller =
      spawn(fn ->
        {:ok, _reservation} = LoginLimiter.reserve(email)
        send(parent, :reserved)

        receive do
          :stop -> :ok
        end
      end)

    assert_receive :reserved, 5_000
    assert LoginLimiter.reserve(email) == :rate_limited

    monitor = Process.monitor(caller)
    Process.exit(caller, :kill)
    assert_receive {:DOWN, ^monitor, :process, ^caller, :killed}, 5_000

    released = await_reservation(email)
    assert LoginLimiter.cancel(released) == :ok
    Enum.each(reservations, &LoginLimiter.cancel/1)
  end

  test "finishing twice does not count a failed attempt twice" do
    email = "duplicate-#{System.unique_integer([:positive])}@test.com"
    {:ok, reservation} = LoginLimiter.reserve(email)

    assert LoginLimiter.finish(reservation, :failed) == :ok
    assert LoginLimiter.finish(reservation, :failed) == :expired
    assert LoginLimiter.cancel(reservation) == :ok
    assert LoginLimiter.cancel(reservation) == :ok

    for _ <- 1..19 do
      {:ok, reservation} = LoginLimiter.reserve(email)
      assert LoginLimiter.finish(reservation, :failed) == :ok
    end

    assert LoginLimiter.reserve(email) == :rate_limited
  end

  defp await_reservation(email, retries \\ 50)

  defp await_reservation(_email, 0), do: flunk("abandoned reservation was not released")

  defp await_reservation(email, retries) do
    case LoginLimiter.reserve(email) do
      {:ok, reservation} ->
        reservation

      :rate_limited ->
        Process.sleep(10)
        await_reservation(email, retries - 1)
    end
  end
end
