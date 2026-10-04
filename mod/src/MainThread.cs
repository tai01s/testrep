using System;
using System.Collections.Generic;
using System.Threading;

namespace RainDash
{
    /// <summary>Runs work queued from background threads on Unity's main thread (pumped by Plugin.Update).</summary>
    public static class MainThread
    {
        static readonly Queue<Action> queue = new Queue<Action>();

        public static void Post(Action action)
        {
            lock (queue) queue.Enqueue(action);
        }

        /// <summary>Runs <paramref name="func"/> on the main thread and waits for the result (with a timeout).</summary>
        public static T Invoke<T>(Func<T> func, int timeoutMs, T fallback)
        {
            T result = fallback;
            using (var done = new ManualResetEvent(false))
            {
                Post(() =>
                {
                    try { result = func(); }
                    catch (Exception e) { Plugin.Log.LogError(e); }
                    finally
                    {
                        try { done.Set(); } catch (ObjectDisposedException) { }
                    }
                });
                if (!done.WaitOne(timeoutMs)) return fallback;
            }
            return result;
        }

        public static void Pump()
        {
            int budget = 32;
            while (budget-- > 0)
            {
                Action next;
                lock (queue)
                {
                    if (queue.Count == 0) return;
                    next = queue.Dequeue();
                }
                try { next(); }
                catch (Exception e) { Plugin.Log.LogError(e); }
            }
        }
    }
}
