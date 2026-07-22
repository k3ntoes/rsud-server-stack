import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider, createRouter } from "@tanstack/react-router";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "./hooks/useAuth";

// Import all routes
import { rootRoute } from "./routes/__root";
import { Route as IndexRoute } from "./routes/index";
import { Route as LoginRoute } from "./routes/login";
import { protectedRoute } from "./routes/_protected";
import { Route as DashboardRoute } from "./routes/dashboard";
import { Route as RoomsRoute } from "./routes/rooms";
import { Route as ItemsRoute } from "./routes/items";
import { Route as InspectionsRoute } from "./routes/inspections";
import { Route as InspectionDetailRoute } from "./routes/inspection-detail";
import { Route as AnalyticsRoute } from "./routes/analytics";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const routeTree = rootRoute.addChildren([
  IndexRoute,
  LoginRoute,
  protectedRoute.addChildren([
    DashboardRoute,
    RoomsRoute,
    ItemsRoute,
    InspectionsRoute,
    InspectionDetailRoute,
    AnalyticsRoute,
  ]),
]);

const router = createRouter({
  routeTree,
  defaultPreload: "intent",
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}

const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </QueryClientProvider>
    </StrictMode>,
  );
}
