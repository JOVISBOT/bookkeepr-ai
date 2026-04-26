import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { Brain, Zap, TrendingUp, AlertTriangle, CheckCircle } from "lucide-react";

export function AISettings() {
  const [aiStatus] = useState({
    isTraining: false,
    accuracy: 85,
    lastTrained: "2026-04-20",
    modelVersion: "v2.1.0",
    totalPredictions: 1234,
  });

  const [categories] = useState([
    { name: "Consulting Revenue", confidence: 95, count: 45 },
    { name: "Marketing", confidence: 92, count: 23 },
    { name: "Software", confidence: 88, count: 12 },
    { name: "Office Supplies", confidence: 85, count: 8 },
    { name: "Travel", confidence: 82, count: 15 },
  ]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">AI Settings</h1>
        <p className="text-slate-500">Configure and monitor your AI categorization engine</p>
      </div>

      {/* AI Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-purple-600" />
            AI Engine Status
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${aiStatus.isTraining ? 'bg-yellow-400 animate-pulse' : 'bg-green-500'}`} />
              <span className="font-medium">{aiStatus.isTraining ? 'Training...' : 'Active'}</span>
            </div>
            <Badge variant="outline">Model {aiStatus.modelVersion}</Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Accuracy</span>
              <span className="font-medium">{aiStatus.accuracy}%</span>
            </div>
            <Progress value={aiStatus.accuracy} className="h-2" />
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-slate-500">Last Trained</p>
              <p className="font-medium">{aiStatus.lastTrained}</p>
            </div>
            <div>
              <p className="text-slate-500">Total Predictions</p>
              <p className="font-medium">{aiStatus.totalPredictions}</p>
            </div>
          </div>

          <Button 
            className="w-full gap-2"
            disabled={aiStatus.isTraining}
          >
            <Zap className="h-4 w-4" />
            {aiStatus.isTraining ? 'Training in Progress...' : 'Retrain Model'}
          </Button>
        </CardContent>
      </Card>

      {/* Category Performance */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-blue-600" />
            Category Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {categories.map((cat) => (
              <div key={cat.name} className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="flex items-center gap-2">
                    {cat.confidence >= 90 ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : cat.confidence >= 80 ? (
                      <AlertTriangle className="h-4 w-4 text-yellow-500" />
                    ) : (
                      <AlertTriangle className="h-4 w-4 text-red-500" />
                    )}
                    {cat.name}
                  </span>
                  <span className="font-medium">{cat.confidence}% ({cat.count} transactions)</span>
                </div>
                <Progress value={cat.confidence} className="h-2" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
