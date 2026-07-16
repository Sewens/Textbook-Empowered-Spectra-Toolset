import { describe, expect, it } from "vitest"

import { toolRoutes } from "./routes"

describe("catalog routes", () => {
  it("allows ordinary readers to browse asserted claims", () => {
    const claims = toolRoutes.find((route) => route.key === "claims")
    expect(claims?.requiredPermission).toBe("evidence:read")
  })
})
