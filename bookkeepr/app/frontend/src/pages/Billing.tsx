import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { getPlans, getSubscription, createCheckout } from "@/lib/api";

const plans = [
  {
    id: "standard",
    name: "Standard",
    price: 199,
    description: "Perfect for small businesses with QBO",
    features: [
      "QBO Integration",
      "AI Categorization",
      "Dashboard & Analytics",
      "Email Support",
      "Up to 1,000 transactions/month",
    ],
  },
  {
    id: "silver",
    name: "Silver",
    price: 299,
    description: "For growing businesses needing QBD",
    features: [
      "Everything in Standard",
      "QBD Integration",
      "Bank Reconciliation",
      "Priority Support",
      "Up to 5,000 transactions/month",
    ],
    popular: true,
  },
  {
    id: "gold",
    name: "Gold",
    price: 399,
    description: "For multi-company operations",
    features: [
      "Everything in Silver",
      "Multi-Company Support",
      "API Access",
      "Dedicated Support",
      "Unlimited transactions",
    ],
  },
];

export function Billing() {
  const { toast } = useToast();
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const { data: subscription, isLoading: subLoading } = useQuery({
    queryKey: ["subscription"],
    queryFn: getSubscription,
  });

  const checkoutMutation = useMutation({
    mutationFn: (planType: string) => createCheckout(planType),
    onSuccess: (data) => {
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: () => {
      toast({
        title: "Error",
        description: "Failed to start checkout. Please try again.",
        variant: "destructive",
      });
    },
  });

  const handleSubscribe = (planId: string) => {
    setSelectedPlan(planId);
    checkoutMutation.mutate(planId);
  };

  if (subLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  const currentPlan = subscription?.subscription?.plan_type;
  const isActive = subscription?.has_active_subscription;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Billing</h1>
        <p className="text-muted-foreground">
          Manage your subscription and billing details
        </p>
      </div>

      {isActive && (
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Current Plan: <Badge variant="default" className="capitalize">{currentPlan}</Badge>
            </CardTitle>
            <CardDescription>
              Your subscription is active and will renew automatically
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      <Tabs defaultValue="plans" className="space-y-6">
        <TabsList>
          <TabsTrigger value="plans">Plans</TabsTrigger>
          {isActive && <TabsTrigger value="manage">Manage</TabsTrigger>}
        </TabsList>

        <TabsContent value="plans" className="space-y-6">
          <div className="grid gap-6 lg:grid-cols-3">
            {plans.map((plan) => (
              <Card key={plan.id} className={plan.popular ? "border-primary" : ""}>
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge variant="default">Most Popular</Badge>
                  </div>
                )}
                <CardHeader>
                  <CardTitle>{plan.name}</CardTitle>
                  <CardDescription>{plan.description}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="text-center">
                    <span className="text-4xl font-bold">${plan.price}</span>
                    <span className="text-muted-foreground">/month</span>
                  </div>
                  <Separator />
                  <ul className="space-y-2 text-sm">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-primary" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
                <CardFooter>
                  <Button
                    className="w-full"
                    variant={currentPlan === plan.id ? "secondary" : "default"}
                    disabled={currentPlan === plan.id || checkoutMutation.isPending}
                    onClick={() => handleSubscribe(plan.id)}
                  >
                    {checkoutMutation.isPending && selectedPlan === plan.id ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Redirecting...
                      </>
                    ) : currentPlan === plan.id ? (
                      "Current Plan"
                    ) : (
                      "Subscribe"
                    )}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </TabsContent>

        {isActive && (
          <TabsContent value="manage">
            <Card>
              <CardHeader>
                <CardTitle>Manage Subscription</CardTitle>
                <CardDescription>
                  Update or cancel your subscription
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-muted-foreground">
                  To cancel your subscription, contact support or use the button below.
                </p>
              </CardContent>
              <CardFooter className="flex gap-4">
                <Button variant="outline">Update Payment Method</Button>
                <Button variant="destructive">Cancel Subscription</Button>
              </CardFooter>
            </Card>
          </TabsContent>
        )}
      </Tabs>
    </div>
  );
}
