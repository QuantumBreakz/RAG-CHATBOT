import React, { useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { Activity, Bell, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { Api } from '../lib/api';

interface HealthCheck {
  component: string;
  status: 'healthy' | 'warning' | 'critical' | 'unknown';
  message: string;
  timestamp: string;
}

interface AlertItem {
  id: string;
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  message: string;
  component: string;
  timestamp: string;
}

const StatusPill: React.FC<{ status: string }> = ({ status }) => {
  const color = status === 'healthy' ? 'bg-green-100 text-green-800' : status === 'warning' ? 'bg-yellow-100 text-yellow-800' : status === 'critical' ? 'bg-red-100 text-red-800' : 'bg-gray-100 text-gray-800';
  return <span className={`px-2 py-1 rounded text-xs ${color}`}>{status}</span>;
};

const MonitoringPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<Record<string, string>>({});
  const [checks, setChecks] = useState<HealthCheck[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const healthResp = await Api.get<any>('/api/monitor/health');
      const historyResp = await Api.get<any>('/api/monitor/health/history');
      const alertsResp = await Api.get<any>('/api/monitor/alerts');

      // Build component -> status map from health_checks list
      const healthMap: Record<string, string> = {};
      const checksList = Array.isArray(healthResp?.health_checks) ? healthResp.health_checks : [];
      checksList.forEach((c: any) => {
        if (c?.component && c?.status) healthMap[c.component] = c.status;
      });
      setHealth(healthMap);

      const historyList: HealthCheck[] = Array.isArray(historyResp?.health_history) ? historyResp.health_history.map((h: any) => ({
        component: h.component,
        status: h.status,
        message: h.message,
        timestamp: h.timestamp,
      })) : [];
      setChecks(historyList);

      const alertsList: AlertItem[] = Array.isArray(alertsResp?.active_alerts) ? alertsResp.active_alerts.map((a: any) => ({
        id: a.id,
        type: a.type,
        severity: a.severity,
        message: a.message,
        component: a.component,
        timestamp: a.timestamp,
      })) : [];
      setAlerts(alertsList);
    } catch (e: any) {
      setErrorMsg(e?.message || 'Failed to load monitoring data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 15000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Monitoring</h1>
            <p className="text-muted-foreground">Real-time system health and alerts</p>
          </div>
          <Button onClick={load} isLoading={loading} className="flex items-center">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>

        {errorMsg && (
          <div className="mb-6 p-3 rounded bg-red-100 text-red-800 border border-red-200 text-sm">{errorMsg}</div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="p-6 lg:col-span-2">
            <h2 className="text-lg font-semibold mb-4 flex items-center"><Activity className="h-5 w-5 mr-2" /> Health Status</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {Object.entries(health).map(([component, status]) => (
                <div key={component} className="flex items-center justify-between p-3 border border-border rounded">
                  <span className="font-medium">{component}</span>
                  <StatusPill status={String(status)} />
                </div>
              ))}
              {Object.keys(health).length === 0 && (
                <div className="text-sm text-muted-foreground">No components reported.</div>
              )}
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center"><Bell className="h-5 w-5 mr-2" /> Active Alerts</h2>
            <div className="space-y-3 max-h-80 overflow-auto">
              {alerts.length === 0 && <div className="text-sm text-muted-foreground">No active alerts</div>}
              {alerts.map((a) => (
                <div key={a.id} className="p-3 border border-border rounded">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">{a.component}</span>
                    <span className="text-xs">{new Date(a.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{a.message}</span>
                    <StatusPill status={a.severity === 'error' ? 'critical' : a.severity} />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <Card className="p-6 mt-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center"><CheckCircle2 className="h-5 w-5 mr-2" /> Recent Health Checks</h2>
          <div className="space-y-3 max-h-96 overflow-auto">
            {checks.length === 0 && <div className="text-sm text-muted-foreground">No health checks recorded</div>}
            {checks.map((hc, idx) => (
              <div key={idx} className="p-3 border border-border rounded">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{hc.component}</span>
                  <StatusPill status={hc.status} />
                </div>
                <div className="text-sm text-muted-foreground flex items-center justify-between">
                  <span>{hc.message}</span>
                  <span className="text-xs">{new Date(hc.timestamp).toLocaleString()}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default MonitoringPage;
