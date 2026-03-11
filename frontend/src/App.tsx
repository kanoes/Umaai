import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./layout/AppShell";
import { AdminPage } from "./pages/AdminPage";
import { CharacterDetailPage } from "./pages/CharacterDetailPage";
import { ComparePage } from "./pages/ComparePage";
import { HomePage } from "./pages/HomePage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RankingsPage } from "./pages/RankingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="characters/:slug" element={<CharacterDetailPage />} />
        <Route path="rankings" element={<RankingsPage />} />
        <Route path="compare" element={<ComparePage />} />
        <Route path="admin" element={<AdminPage />} />
        <Route path="home" element={<Navigate replace to="/" />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
