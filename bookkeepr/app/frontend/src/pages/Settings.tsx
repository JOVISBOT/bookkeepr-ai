import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Switch } from "../components/ui/switch";
import { User, Bell, Shield, Database } from "lucide-react";

export function SettingsPage() {
  const [settings, setSettings] = useState({
    emailNotifications: true,
    autoCategorize: true,
    darkMode: false,
    twoFactor: false,
  });

  const [profile, setProfile] = useState({
    name: "Jo Vany",
    email: "jo@bookkeepr.ai",
    company: "BookKeepr AI"
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500">Manage your account and preferences</p>
      </div>

      {/* Profile Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <User className="h-5 w-5" />
            Profile
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700">Name</label>
              <Input 
                value={profile.name}
                onChange={(e) => setProfile({...profile, name: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Email</label>
              <Input 
                value={profile.email}
                onChange={(e) => setProfile({...profile, email: e.target.value})}
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700">Company</label>
              <Input 
                value={profile.company}
                onChange={(e) => setProfile({...profile, company: e.target.value})}
              />
            </div>
          </div>
          <Button>Save Profile</Button>
        </CardContent>
      </Card>

      {/* Notification Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5" />
            Notifications
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Email Notifications</p>
              <p className="text-sm text-slate-500">Receive email updates about your account</p>
            </div>
            <Switch 
              checked={settings.emailNotifications}
              onCheckedChange={(checked) => setSettings({...settings, emailNotifications: checked})}
            />
          </div>
        </CardContent>
      </Card>

      {/* AI Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5" />
            AI Configuration
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Auto-Categorization</p>
              <p className="text-sm text-slate-500">Automatically categorize new transactions</p>
            </div>
            <Switch 
              checked={settings.autoCategorize}
              onCheckedChange={(checked) => setSettings({...settings, autoCategorize: checked})}
            />
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Security
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">Two-Factor Authentication</p>
              <p className="text-sm text-slate-500">Add an extra layer of security</p>
            </div>
            <Switch 
              checked={settings.twoFactor}
              onCheckedChange={(checked) => setSettings({...settings, twoFactor: checked})}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
