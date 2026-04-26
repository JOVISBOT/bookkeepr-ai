// @ts-nocheck
import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

export function QuickBooksConnect() {
  const [status, setStatus]: any = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [error, setError]: any = useState(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response: any = await api.get('/integrations/quickbooks/status');
      setStatus(response.data);
    } catch (err) {
      setStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    setConnecting(true);
    setError(null);
    
    try {
      const response: any = await api.get('/integrations/quickbooks/auth-url');
      const authUrl = response.data.auth_url;
      
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;
      
      const popup: any = window.open(
        authUrl,
        'QuickBooks OAuth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      const handleMessage = (event: any) => {
        if (event.data?.type === 'qb-connected') {
          window.removeEventListener('message', handleMessage);
          popup?.close();
          checkStatus();
        }
      };
      
      window.addEventListener('message', handleMessage);
      
      const checkClosed = setInterval(() => {
        if (popup?.closed) {
          clearInterval(checkClosed);
          window.removeEventListener('message', handleMessage);
          setConnecting(false);
        }
      }, 1000);
      
    } catch (err: any) {
      setError('Failed to start QuickBooks connection');
      setConnecting(false);
    }
  };

  const handleSync = async () => {
    setLoading(true);
    try {
      await api.post('/integrations/quickbooks/sync');
      checkStatus();
    } catch (err: any) {
      setError('Sync failed');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          QuickBooks Online
          {status?.connected && <CheckCircle className="h-5 w-5 text-green-500" />}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {error && (
          <div className="flex items-center gap-2 text-red-500 text-sm">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}
        
        {status?.connected ? (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Connected to QuickBooks
            </p>
            {status.last_sync && (
              <p className="text-xs text-muted-foreground">
                Last sync: {new Date(status.last_sync).toLocaleString()}
              </p>
            )}
            <Button 
              onClick={handleSync} 
              disabled={loading}
              className="w-full"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Sync Transactions'}
            </Button>
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Connect your QuickBooks Online account to sync transactions
            </p>
            <Button 
              onClick={handleConnect} 
              disabled={connecting}
              className="w-full"
            >
              {connecting ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Connect QuickBooks'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
