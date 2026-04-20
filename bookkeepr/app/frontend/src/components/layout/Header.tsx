import { useLocation } from "react-router-dom";
import { Button } from "../ui/Button";
import { RefreshCw, Plus } from "lucide-react";

interface HeaderProps {
  onSync?: () => void;
  onAdd?: () => void;
  isSyncing?: boolean;
}

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/transactions": "Transactions",
  "/review": "Review Queue",
  "/companies": "Companies",
  "/ai": "AI Settings",
  "/settings": "Settings",
};

export function Header({ onSync, onAdd, isSyncing }: HeaderProps) {
  const location = useLocation();
  const title = pageTitles[location.pathname] || "BookKeepr";

  return (
    <header className="h-16 border-b bg-white flex items-center justify-between px-8">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <div className="flex items-center gap-2">
        {onSync && (
          <Button
            variant="outline"
            size="sm"
            onClick={onSync}
            disabled={isSyncing}
          >
            <RefreshCw
              className={`h-4 w-4 mr-2 ${isSyncing ? "animate-spin" : ""}`}
            />
            {isSyncing ? "Syncing..." : "Sync"}
          </Button>
        )}
        {onAdd && (
          <Button size="sm" onClick={onAdd}>
            <Plus className="h-4 w-4 mr-2" />
            Add New
          </Button>
        )}
      </div>
    </header>
  );
}
