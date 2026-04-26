import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import { 
  Shield, 
  Lock, 
  Key, 
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  Server,
  Database
} from "lucide-react";

interface SecurityFeature {
  id: string;
  name: string;
  description: string;
  status: "implemented" | "in_progress" | "planned";
  icon: React.ReactNode;
}

const securityFeatures: SecurityFeature[] = [
  {
    id: "encryption",
    name: "End-to-End Encryption",
    description: "AES-256 encryption for all data at rest and in transit",
    status: "implemented",
    icon: <Lock className="h-5 w-5" />,
  },
  {
    id: "local_storage",
    name: "Local-Only Storage",
    description: "Data never leaves your machine - SQLite database",
    status: "implemented",
    icon: <Database className="h-5 w-5" />,
  },
  {
    id: "auth",
    name: "JWT Authentication",
    description: "Secure token-based authentication with expiry",
    status: "implemented",
    icon: <Key className="h-5 w-5" />,
  },
  {
    id: "https",
    name: "HTTPS/TLS 1.3",
    description: "All communications encrypted with latest TLS",
    status: "implemented",
    icon: <Shield className="h-5 w-5" />,
  },
  {
    id: "mfa",
    name: "Multi-Factor Auth",
    description: "Optional MFA for additional account security",
    status: "in_progress",
    icon: <Key className="h-5 w-5" />,
  },
  {
    id: "audit",
    name: "Audit Logging",
    description: "Complete audit trail of all data access",
    status: "planned",
    icon: <Server className="h-5 w-5" />,
  },
  {
    id: "rate_limit",
    name: "Rate Limiting",
    description: "API rate limiting to prevent abuse",
    status: "planned",
    icon: <Shield className="h-5 w-5" />,
  },
  {
    id: "backup",
    name: "Encrypted Backups",
    description: "Automatic encrypted backups to secure storage",
    status: "planned",
    icon: <Database className="h-5 w-5" />,
  },
];

export function SecurityStatus() {
  const [showDetails, setShowDetails] = useState(false);

  const implemented = securityFeatures.filter(f => f.status === "implemented").length;
  const inProgress = securityFeatures.filter(f => f.status === "in_progress").length;
  const planned = securityFeatures.filter(f => f.status === "planned").length;

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <Shield className="h-6 w-6 text-green-600" />
          <h2 className="text-2xl font-bold text-slate-900">Security Status</h2>
        </div>
        <p className="text-slate-500">
          Your data is protected with industry-standard security measures
        </p>
      </div>

      {/* Security Overview */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4 text-center">
            <CheckCircle2 className="h-8 w-8 text-green-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-green-700">{implemented}</div>
            <div className="text-sm text-green-600">Implemented</div>
          </CardContent>
        </Card>

        <Card className="bg-amber-50 border-amber-200">
          <CardContent className="p-4 text-center">
            <AlertTriangle className="h-8 w-8 text-amber-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-amber-700">{inProgress}</div>
            <div className="text-sm text-amber-600">In Progress</div>
          </CardContent>
        </Card>

        <Card className="bg-slate-50 border-slate-200">
          <CardContent className="p-4 text-center">
            <Eye className="h-8 w-8 text-slate-600 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-700">{planned}</div>
            <div className="text-sm text-slate-600">Planned</div>
          </CardContent>
        </Card>
      </div>

      {/* Security Features List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Security Features</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? (
                <><EyeOff className="h-4 w-4 mr-2" />Hide Details</>
              ) : (
                <><Eye className="h-4 w-4 mr-2" />Show Details</>
              )}
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {securityFeatures.map((feature) => (
              <div
                key={feature.id}
                className="flex items-center justify-between p-3 rounded-lg border hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-slate-100 rounded-lg">{feature.icon}</div>
                  <div>
                    <p className="font-medium text-slate-900">{feature.name}</p>
                    {showDetails && (
                      <p className="text-sm text-slate-500">{feature.description}</p>
                    )}
                  </div>
                </div>
                <Badge
                  variant={
                    feature.status === "implemented"
                      ? "success"
                      : feature.status === "in_progress"
                      ? "default"
                      : "secondary"
                  }
                >
                  {feature.status === "implemented"
                    ? "Active"
                    : feature.status === "in_progress"
                    ? "In Progress"
                    : "Planned"}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Data Protection Notice */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <p className="font-medium text-blue-900">Your Data Stays Local</p>
              <p className="text-sm text-blue-700 mt-1">
                BookKeepr stores all your data locally on your machine. 
                No financial data is sent to external servers unless you 
                explicitly connect to QuickBooks or other integrations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
