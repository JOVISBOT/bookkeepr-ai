import { NavLink } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  LayoutDashboard,
  Receipt,
  CheckCircle,
  Settings,
  Building2,
  Brain,
  FileText,
} from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/transactions", icon: Receipt, label: "Transactions" },
  { to: "/review", icon: CheckCircle, label: "Review Queue" },
  { to: "/reconciliation", icon: FileText, label: "Reconciliation" },
  { to: "/companies", icon: Building2, label: "Companies" },
  { to: "/ai", icon: Brain, label: "AI Settings" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <div className="w-64 bg-slate-900 text-white flex flex-col h-screen fixed left-0 top-0">
      <div className="p-6">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center font-bold">
            B
          </div>
          <span className="text-xl font-bold">BookKeepr</span>
        </div>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-colors",
                isActive
                  ? "bg-blue-600 text-white"
                  : "text-slate-300 hover:bg-slate-800 hover:text-white"
              )
            }
          >
            <item.icon className="h-5 w-5" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-4 py-3">
          <div className="w-8 h-8 bg-slate-700 rounded-full flex items-center justify-center text-sm font-medium">
            U
          </div>
          <div className="text-sm">
            <div className="font-medium">User</div>
            <div className="text-slate-400 text-xs">Connected</div>
          </div>
        </div>
      </div>
    </div>
  );
}
