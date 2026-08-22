import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { HomePage } from "@/pages/home/HomePage";
import { DocsPage } from "@/pages/docs/DocsPage";
import { CodebotPage } from "@/pages/codebot/CodebotPage";
import { NeroLayout } from "@/pages/nero/NeroLayout";
import { AnalyticsPage } from "@/pages/nero/AnalyticsPage";
import { MemoryPage } from "@/pages/nero/MemoryPage";
import { PRReviewsPage } from "@/pages/nero/PRReviewsPage";
import { SettingsPage } from "@/pages/nero/SettingsPage";
import { LoginPage } from "@/pages/auth/LoginPage";
import { SignupPage } from "@/pages/auth/SignupPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        {/* Landing Page */}
        <Route path="/" element={<HomePage />} />

        {/* Documentation Hub */}
        <Route path="/docs" element={<DocsPage />} />

        {/* Codebot Interactive Chat & Workspace */}
        <Route path="/codebot" element={<CodebotPage />} />

        {/* Nero AI Dashboard Suite */}
        <Route path="/nero" element={<NeroLayout />}>
          <Route index element={<Navigate to="/nero/analytics" replace />} />
          <Route path="analytics" element={<AnalyticsPage />} />
          <Route path="memory" element={<MemoryPage />} />
          <Route path="pr-reviews" element={<PRReviewsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Auth Pages */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        {/* Catch-all fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
