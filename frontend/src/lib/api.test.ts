import { describe, expect, it, vi } from "vitest";
import { fetchJson, resolveApiUrl } from "./api";

describe("api helpers", () => {
  it("fetchJson resolves JSON payloads", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchJson<{ status: string }>("/api/health");

    expect(result.status).toBe("ok");
    expect(fetchMock).toHaveBeenCalledWith(resolveApiUrl("/api/health"));
  });

  it("fetchJson throws on non-200 responses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        statusText: "Not Found",
      }),
    );

    await expect(fetchJson("/api/missing")).rejects.toThrow("Request failed: 404 Not Found");
  });
});
