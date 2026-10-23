import { afterEach, describe, expect, it, vi } from 'vitest';
import { parseEvent, streamChat, waitForBackend } from './api';

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers(); });
describe('stream protocol', () => {
  it('preserves Arabic and ignores comments', () => {
    expect(parseEvent('event: delta\ndata: {"text":"مرحبا"}')?.data.text).toBe('مرحبا');
    expect(parseEvent(': ping')).toBeNull();
  });
  it('handles network chunks split within an Arabic character', async () => {
    const bytes = new TextEncoder().encode('event: delta\ndata: {"text":"مرحبا"}\n\nevent: done\ndata: {"answer":"مرحبا","sources":[]}\n\n');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(new ReadableStream({ start(controller) { for (let i = 0; i < bytes.length; i += 7) controller.enqueue(bytes.slice(i, i + 7)); controller.close(); } }))));
    const events: string[] = [];
    await streamChat({}, new AbortController().signal, e => events.push(e.kind));
    expect(events).toEqual(['delta', 'done']);
  });
  it('rejects incomplete answers', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('event: delta\ndata: {"text":"partial"}\n\n')));
    await expect(streamChat({}, new AbortController().signal, () => {})).rejects.toThrow('interrupted');
  });
  it('surfaces quota errors without treating a draft as complete', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('event: error\ndata: {"code":"quota"}\n\n')));
    await expect(streamChat({}, new AbortController().signal, () => {})).rejects.toThrow('quota');
  });
});
describe('cold start', () => {
  it('polls until ready', async () => {
    vi.useFakeTimers();
    const fetch = vi.fn().mockRejectedValueOnce(new TypeError('asleep')).mockResolvedValue(new Response('{"status":"ok"}'));
    vi.stubGlobal('fetch', fetch);
    const notify = vi.fn(); const work = waitForBackend(new AbortController().signal, notify);
    await vi.advanceTimersByTimeAsync(2500);
    await expect(work).resolves.toMatchObject({ status: 'ok' });
    expect(notify).toHaveBeenCalledOnce();
  });
  it('stops polling at the configured deadline', async () => {
    vi.useFakeTimers(); vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
    const work = expect(waitForBackend(new AbortController().signal, () => {}, 5000)).rejects.toThrow('wake_timeout');
    await vi.advanceTimersByTimeAsync(5000); await work;
  });
  it('cancels without waiting for the full wake budget', async () => {
    vi.useFakeTimers(); vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('asleep')));
    const controller = new AbortController();
    const work = expect(waitForBackend(controller.signal, () => {})).rejects.toThrow();
    await vi.advanceTimersByTimeAsync(1); controller.abort(); await work;
  });
});
