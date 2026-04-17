import { Navigate, Route, Routes } from "react-router-dom";
import { DashboardLayout } from "./layouts/DashboardLayout";
import { ComparisonPage } from "./pages/ComparisonPage";
import { GenerationPage } from "./pages/GenerationPage";
import { HomePage } from "./pages/HomePage";
import { ProductsPage } from "./pages/ProductsPage";
import { ProfilesPage } from "./pages/ProfilesPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { WorkflowPage } from "./pages/WorkflowPage";

function App() {
  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/products" element={<ProductsPage />} />
        <Route path="/reviews" element={<ReviewsPage />} />
        <Route path="/profiles" element={<ProfilesPage />} />
        <Route path="/generation" element={<GenerationPage />} />
        <Route path="/comparison" element={<ComparisonPage />} />
        <Route path="/workflow" element={<WorkflowPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DashboardLayout>
  );
}

export default App;

