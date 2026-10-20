import { StrictMode, Suspense, lazy, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./styles.css";
import { AuthProvider, PlaceProvider, RequireUser, ScopedPick, useAuth, usePlace } from "./auth";
import { DataProvider } from "./data";
import { I18nProvider } from "./i18n";
import { PrefsProvider } from "./prefs";
import { Loader } from "./ui/parts";
import { Shell } from "./ui/Shell";

const Landing = lazy(() => import("./pages/Landing"));
const Login = lazy(() => import("./pages/Login"));
const Method = lazy(() => import("./pages/Method"));
const India = lazy(() => import("./pages/India"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Explore = lazy(() => import("./pages/Explore"));
const Plan = lazy(() => import("./pages/Plan"));
const Ask = lazy(() => import("./pages/Ask"));
const Settings = lazy(() => import("./pages/Settings"));

function PersonalPrefs({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  return <PrefsProvider owner={user?.id ?? "guest"}>{children}</PrefsProvider>;
}

function PlaceData({ children }: { children: ReactNode }) {
  const [place] = usePlace();
  return <DataProvider state={place} fallback={<Loader />}>{children}</DataProvider>;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider fallback={<Loader />}>
        <PersonalPrefs>
          <I18nProvider>
            <PlaceProvider>
              <PlaceData>
                <ScopedPick>
                  <Suspense fallback={<Loader />}>
                    <Routes>
                      <Route element={<Shell />}>
                        <Route path="/" element={<Landing />} />
                        <Route path="/login" element={<Login />} />
                        <Route path="/method" element={<Method />} />
                        <Route element={<RequireUser />}>
                          <Route path="/india" element={<India />} />
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/explore" element={<Explore />} />
                          <Route path="/plan" element={<Plan />} />
                          <Route path="/ask" element={<Ask />} />
                          <Route path="/settings" element={<Settings />} />
                        </Route>
                        <Route path="*" element={<Navigate to="/dashboard" replace />} />
                      </Route>
                    </Routes>
                  </Suspense>
                </ScopedPick>
              </PlaceData>
            </PlaceProvider>
          </I18nProvider>
        </PersonalPrefs>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
);
