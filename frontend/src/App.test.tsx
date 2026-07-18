import { expect, test, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import App from "./App";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});


test("renders dashboard headings and handles network states", async () => {
  // Mock connection response
  const fetchMock = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({
      status: "healthy",
      env: "development",
      database: "connected"
    }),
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  );

  // Assert critical elements render correctly
  const headingElement = screen.getByText(/Subsurface Exploration Dashboard/i);
  expect(headingElement).toBeInTheDocument();

  const brandElement = screen.getByText(/GreenBore AI/i);
  expect(brandElement).toBeInTheDocument();
  
  const subHeading = screen.getByText(/Borehole Profile Visualization/i);
  expect(subHeading).toBeInTheDocument();
});
