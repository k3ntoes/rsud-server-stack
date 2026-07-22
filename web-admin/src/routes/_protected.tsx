import { createRoute } from "@tanstack/react-router";
import { rootRoute } from "./__root";
import Layout from "../components/Layout";

export const protectedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: "protected",
  component: Layout,
});
