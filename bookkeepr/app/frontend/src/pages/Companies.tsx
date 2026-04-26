import { useState } from "react";
import { Card, CardContent } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Building2, Plus, Search, Edit, Trash2 } from "lucide-react";

interface Company {
  id: number;
  name: string;
  industry: string;
  created_at: string;
}

export function Companies() {
  const [companies, setCompanies] = useState<Company[]>([
    { id: 1, name: "Acme Consulting", industry: "Consulting", created_at: "2026-01-15" },
    { id: 2, name: "TechStart Inc", industry: "Technology", created_at: "2026-02-20" },
  ]);
  const [searchTerm, setSearchTerm] = useState("");
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: "", industry: "" });

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    c.industry.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleAddCompany = () => {
    if (newCompany.name && newCompany.industry) {
      setCompanies([...companies, {
        id: companies.length + 1,
        name: newCompany.name,
        industry: newCompany.industry,
        created_at: new Date().toISOString().split('T')[0]
      }]);
      setNewCompany({ name: "", industry: "" });
      setShowAddForm(false);
    }
  };

  const handleDeleteCompany = (id: number) => {
    setCompanies(companies.filter(c => c.id !== id));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Companies</h1>
          <p className="text-slate-500">Manage your client companies</p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)} className="gap-2">
          <Plus className="h-4 w-4" />
          Add Company
        </Button>
      </div>

      {showAddForm && (
        <Card>
          <CardContent className="p-4">
            <div className="flex gap-4 items-end">
              <div className="flex-1">
                <label className="text-sm font-medium text-slate-700">Company Name</label>
                <Input 
                  value={newCompany.name}
                  onChange={(e) => setNewCompany({...newCompany, name: e.target.value})}
                  placeholder="Enter company name"
                />
              </div>
              <div className="flex-1">
                <label className="text-sm font-medium text-slate-700">Industry</label>
                <Input 
                  value={newCompany.industry}
                  onChange={(e) => setNewCompany({...newCompany, industry: e.target.value})}
                  placeholder="Enter industry"
                />
              </div>
              <Button onClick={handleAddCompany}>Add</Button>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input 
          className="pl-10"
          placeholder="Search companies..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      <div className="grid gap-4">
        {filteredCompanies.map((company) => (
          <Card key={company.id}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Building2 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900">{company.name}</h3>
                    <p className="text-sm text-slate-500">{company.industry} • Added {company.created_at}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="gap-1">
                    <Edit className="h-4 w-4" />
                    Edit
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="gap-1 text-red-600 hover:bg-red-50"
                    onClick={() => handleDeleteCompany(company.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
