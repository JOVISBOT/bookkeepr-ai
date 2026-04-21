import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "../lib/api";
import { getAccounts } from "../lib/api";

// Cache times (ms)
const CACHE_TIMES = {
  COMPANIES: 1000 * 60 * 30,      // 30 min - rarely changes
  ACCOUNTS: 1000 * 60 * 15,       // 15 min - changes occasionally
};

// Get companies
export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: getCompanies,
    staleTime: CACHE_TIMES.COMPANIES,
    gcTime: CACHE_TIMES.COMPANIES * 2,
  });
}

// Get accounts
export function useAccounts(companyId: number | null, type?: string) {
  return useQuery({
    queryKey: ["accounts", companyId, type],
    queryFn: () => {
      if (!companyId) throw new Error("Company ID required");
      return getAccounts(companyId, type);
    },
    enabled: !!companyId,
    staleTime: CACHE_TIMES.ACCOUNTS,
    gcTime: CACHE_TIMES.ACCOUNTS * 2,
  });
}
