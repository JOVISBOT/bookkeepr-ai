import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "./components/layout";
import { Dashboard } from "./pages/Dashboard";
import { Transactions } from "./pages/Transactions";
import { ReviewPage } from "./pages/ReviewPage";
import { Reconciliation } from "./pages/Reconciliation";
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
    </QueryClientProvider>
  );
}

export default App;
