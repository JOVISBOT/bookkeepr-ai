import { useQuery } from "@tanstack/react-query";
import { getCompanies } from "../lib/api";
import { getAccounts } from "../lib/api";

// Get companies
export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: getCompanies,
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
  });
}
