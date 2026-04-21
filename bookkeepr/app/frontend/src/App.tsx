import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout";
import { Toaster } from "./components/ui/toaster";
import { Dashboard } from "./pages/Dashboard";
import { Transactions } from "./pages/Transactions";
import { ReviewPage } from "./pages/ReviewPage";
import { Reconciliation } from "./pages/Reconciliation";
import { Billing } from "./pages/Billing";
import { useState } from "react";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

function AppContent() {
  const [isSyncing, setIsSyncing] = useState(false);

  const handleSync = async () => {
    // Would need to get current company ID from context/state
    // For now, this is a placeholder
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
          <Route path="/reconciliation" element={<Reconciliation />} />
          <Route path="/reconciliation/:statementId" element={<Reconciliation />} />
          <Route path="/billing" element={<Billing />} />
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
