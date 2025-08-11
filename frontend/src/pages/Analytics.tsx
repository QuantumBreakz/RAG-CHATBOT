import React, { useEffect, useState } from 'react';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import { BarChart3, Activity, Users, AlertTriangle, RefreshCw } from 'lucide-react';
import { Api } from '../lib/api';

interface QueryAnalytics {
  total_queries?: number;
  avg_response_time?: number;
  avg_processing_time?: number;
  avg_chunk_count?: number;
  cache_hit_rate?: number;
}

interface SystemAnalytics {
  avg_cpu_usage?: number;
  avg_memory_usage?: number;
  avg_disk_usage?: number;
  system_health_score?: number;
}

interface UserAnalytics {
  unique_users?: number;
  unique_sessions?: number;
  avg_activities_per_user?: number;
}

interface ErrorAnalytics {
  total_errors?: number;
  error_rate?: number;
}

const Stat: React.FC<{ label: string; value: string | number; icon?: React.ReactNode }> = ({ label, value, icon }) => (
  <Card className="p-5 flex items-center justify-between">
    <div>
      <div className="text-sm text-muted-foreground">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
    <div className="opacity-70">{icon}</div>
  </Card>
);

const AnalyticsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState<QueryAnalytics>({});
  const [system, setSystem] = useState<SystemAnalytics>({});
  const [user, setUser] = useState<UserAnalytics>({});
  const [errors, setErrors] = useState<ErrorAnalytics>({});
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      // These endpoints should be implemented in backend to return analytics snapshots
      const report = await Api.get<any>('/api/analytics/report');
      setQuery(report?.query_analytics || {});
      setSystem(report?.system_analytics || {});
      setUser(report?.user_analytics || {});
      setErrors(report?.error_analytics || {});
    } catch (e: any) {
      setErrorMsg(e?.message || 'Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 30000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-muted-foreground">System, query, user and error analytics</p>
          </div>
          <Button onClick={load} isLoading={loading} className="flex items-center">
            <RefreshCw className="h-4 w-4 mr-2" /> Refresh
          </Button>
        </div>

        {errorMsg && (
          <div className="mb-6 p-3 rounded bg-red-100 text-red-800 border border-red-200 text-sm">{errorMsg}</div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <Stat label="Total Queries" value={query.total_queries ?? 0} icon={<BarChart3 className="h-6 w-6" />} />
          <Stat label="Avg Response (s)" value={(query.avg_response_time ?? 0).toFixed(2)} icon={<Activity className="h-6 w-6" />} />
          <Stat label="Cache Hit Rate" value={`${Math.round((query.cache_hit_rate ?? 0) * 100)}%`} icon={<BarChart3 className="h-6 w-6" />} />
          <Stat label="Health Score" value={Math.round(system.system_health_score ?? 100)} icon={<Activity className="h-6 w-6" />} />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center"><Activity className="h-5 w-5 mr-2" /> System</h2>
            <div className="grid grid-cols-2 gap-4">
              <Stat label="CPU (%)" value={(system.avg_cpu_usage ?? 0).toFixed(1)} />
              <Stat label="Memory (%)" value={(system.avg_memory_usage ?? 0).toFixed(1)} />
              <Stat label="Disk (%)" value={(system.avg_disk_usage ?? 0).toFixed(1)} />
              <Stat label="Health" value={Math.round(system.system_health_score ?? 100)} />
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center"><Users className="h-5 w-5 mr-2" /> Users</h2>
            <div className="grid grid-cols-2 gap-4">
              <Stat label="Unique Users" value={user.unique_users ?? 0} />
              <Stat label="Sessions" value={user.unique_sessions ?? 0} />
              <Stat label="Avg Actions/User" value={(user.avg_activities_per_user ?? 0).toFixed(1)} />
            </div>
          </Card>

          <Card className="p-6">
            <h2 className="text-lg font-semibold mb-4 flex items-center"><AlertTriangle className="h-5 w-5 mr-2" /> Errors</h2>
            <div className="grid grid-cols-2 gap-4">
              <Stat label="Total Errors" value={errors.total_errors ?? 0} />
              <Stat label="Error Rate" value={`${Math.round((errors.error_rate ?? 0) * 100)}%`} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;

