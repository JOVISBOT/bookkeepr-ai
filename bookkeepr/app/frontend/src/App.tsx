import { useState, lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout";
import { Toaster } from "./components/ui/toaster";
import { Dashboard } from "./pages/Dashboard";
import { Transactions } from "./pages/Transactions";
import { ReviewPage } from "./pages/ReviewPage";

// Lazy load heavy routes with Recharts (using named exports)
const Reconciliation = lazy(() => import("./pages/Reconciliation").then(m => ({ default: m.Reconciliation })));
const Billing = lazy(() => import("./pages/Billing").then(m => ({ default: m.Billing })));

// Smart cache strategy: different stale times per data type
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes default
      retry: 1,
    },
  },
});

// Per-route cache configuration
export const dashboardQueryConfig = { staleTime: 1000 * 60 * 15 }; // 15 min - rarely changes
export const transactionQueryConfig = { staleTime: 1000 * 60 * 2 }; // 2 min - changes frequently
export const billingQueryConfig = { staleTime: 1000 * 60 * 30 }; // 30 min - subscription data

function AppContent() {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      // await syncMutation.mutateAsync({ companyId: 1, type: "full" });
    } finally {
      setIsSyncing(false);
    }
  };

  return (
    <BrowserRouter>
      <Layout onSync={handleSync} isSyncing={isSyncing}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
          <Route path="/review" element={<ReviewPage />} />
          
          {/* Lazy loaded routes with Suspense */}
          <Route path="/reconciliation" element={
            <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Reconciliation...</div>}>
              <Reconciliation />
            </Suspense>
          } />
          <Route path="/reconciliation/:statementId" element={
            <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Reconciliation...</div>}>
              <Reconciliation />
            </Suspense>
          } />
          <Route path="/billing" element={
            <Suspense fallback={<div className="p-8 text-center text-slate-500">Loading Billing...</div>}>
              <Billing />
            </Suspense>
          } />
          
          {/* Success/Cancel pages - keep light */}
          <Route path="/billing/success" element={
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <h2 className="text-2xl font-bold text-green-600">Payment Successful!</h2>
              <p>Your subscription is now active.</p>
            </div>
          } />
          <Route path="/billing/cancel" element={
            <div className="flex flex-col items-center justify-center h-64 space-y-4">
              <h2 className="text-2xl font-bold text-slate-600">Payment Cancelled</h2>
              <p>You can try again anytime.</p>
            </div>
          } />
          
          <Route
            path="/companies"
            element={
              <div className="flex items-center justify-center h-64 text-slate-500">
                Companies management coming soon
              </div>
            }
          />
          <Route
            path="/ai"
            element={
              <div className="flex items-center justify-center h-64 text-slate-500">
                AI settings coming soon
              </div>
            }
          />
          <Route
            path="/settings"
            element={
              <div className="flex items-center justify-center h-64 text-slate-500">
                Settings coming soon
              </div>
            }
          />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <Toaster />
    </QueryClientProvider>
  );
}

export default App;
