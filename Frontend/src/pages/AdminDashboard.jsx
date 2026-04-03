import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import { 
  Menu, Bell, Search, ShieldAlert, Cpu, 
  TrendingUp, AlertTriangle, Zap, CheckCircle, Database
} from 'lucide-react';
import api from '../api/client';

const COLORS = ['#22c55e', '#f59e0b', '#3b82f6', '#ef4444'];

export default function AdminDashboard() {
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [trends, setTrends] = useState([]);
  const [fraudAlerts, setFraudAlerts] = useState([]);
  const [predictions, setPredictions] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [dataRefresh, setDataRefresh] = useState(0);

  // Demo Trigger form state
  const [demoZone, setDemoZone] = useState('Mumbai');
  const [demoSubZone, setDemoSubZone] = useState('Dadar');
  const [demoTriggerType, setDemoTriggerType] = useState('heavy_rain');
  const [demoValue, setDemoValue] = useState(30);
  const [simulateLog, setSimulateLog] = useState([]);
  const [simulating, setSimulating] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    }

    const loadData = async () => {
      try {
        const [statsRes, trendsRes, fraudRes, predictionsRes] = await Promise.all([
          api.get('/admin/dashboard-stats'),
          api.get('/admin/weekly-trends'),
          api.get('/admin/fraud-alerts'),
          api.get('/admin/predictions')
        ]);
        
        setStats(statsRes.data);
        setTrends(trendsRes.data);
        setFraudAlerts(fraudRes.data);
        setPredictions(predictionsRes.data);
      } catch (err) {
        console.error("Admin dashboard load error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [navigate, dataRefresh]);

  const handleSimulate = async () => {
    setSimulating(true);
    setSimulateLog(['[SYS] Connecting to Parametric Simulator...']);
    try {
      const res = await api.post('/admin/simulate-trigger', {
        city: demoZone,
        zone: demoSubZone,
        trigger_type: demoTriggerType,
        trigger_value: parseFloat(demoValue)
      });
      
      // Animate the log streaming line-by-line instead of instantly dumping
      for (let i = 0; i < res.data.logs.length; i++) {
        await new Promise(r => setTimeout(r, 600)); // fake delay for drama
        setSimulateLog(prev => [...prev, res.data.logs[i]]);
      }
      setDataRefresh(prev => prev + 1);
      
    } catch (err) {
      setSimulateLog(prev => [...prev, `[ERROR] Simulation failed: ${err.message}`]);
    } finally {
      setSimulating(false);
    }
  };

  if (loading || !stats) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <motion.div animate={{ rotate: 180 }} transition={{ repeat: Infinity, duration: 1.5 }}>
          <ShieldAlert className="text-orange-500 w-16 h-16" />
        </motion.div>
      </div>
    );
  }

  // Format Claims by Status for Recharts Pie
  const donutData = Object.entries(stats.claims_by_status).map(([k, v]) => ({
      name: k.replace("_", "-").toUpperCase(),
      value: v
  }));

  // Recharts custom tooltips
  const DarkTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700 p-3 rounded shadow-xl text-slate-300">
          <p className="font-bold text-white mb-1">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color }} className="text-sm">
              {entry.name}: <span className="font-mono">{entry.value}</span>
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-300 font-sans flex">
      {/* SIDEBAR */}
      <div className="w-64 bg-[#1e293b] border-r border-slate-800 flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <ShieldAlert className="text-orange-500 mr-2" size={24}/>
          <span className="text-white font-bold text-lg tracking-wide">ShiftShield HQ</span>
        </div>
        <div className="flex-1 py-6 px-4 space-y-2">
          <button onClick={() => setActiveTab('overview')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'overview' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}><TrendingUp size={18}/> Overview</button>
          <button onClick={() => setActiveTab('risk-models')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'risk-models' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}><ShieldAlert size={18}/> Risk Models</button>
          <button onClick={() => setActiveTab('ai-engine')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'ai-engine' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}><Cpu size={18}/> AI Engine</button>
          <button onClick={() => setActiveTab('policies')} className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${activeTab === 'policies' ? 'bg-slate-800 text-white' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'}`}><Database size={18}/> Policies</button>
        </div>
        <div className="p-4 border-t border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center text-white font-bold text-xs">A</div>
            <span className="text-sm text-white font-medium">Administrator</span>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        
        {/* TOP NAVBAR */}
        <header className="h-16 bg-[#1e293b] border-b border-slate-800 flex items-center justify-between px-6 z-10 shrink-0">
          <div className="flex items-center gap-4">
            <Menu className="md:hidden text-slate-400" size={24}/>
            <div className="relative hidden sm:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16}/>
              <input type="text" placeholder="Search claims, policies..." className="bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-1.5 text-sm text-slate-300 focus:outline-none focus:border-orange-500 w-64"/>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <div className="relative">
              <Bell className="text-slate-400" size={20} />
              <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 border-2 border-[#1e293b] rounded-full"></span>
            </div>
          </div>
        </header>

        {/* DASHBOARD CONTENT SCROLL */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeTab !== 'overview' ? (
            <div className="h-full flex flex-col items-center justify-center text-slate-500 min-h-[60vh]">
               <Cpu className="w-16 h-16 text-slate-700 mb-4 animate-pulse" />
               <h2 className="text-xl font-bold text-white mb-2">{activeTab.replace('-', ' ').toUpperCase()}</h2>
               <p>This module is currently initializing parameters...</p>
            </div>
          ) : (
            <>
              <div className="flex justify-between items-end">
            <div>
              <h1 className="text-2xl font-bold text-white">Platform Analytics</h1>
              <p className="text-slate-500 text-sm mt-1">Live metrics and parametric risk assessment.</p>
            </div>
          </div>

          {/* TOP METRICS ROW */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl">
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Active Policies</p>
              <div className="flex items-end gap-3">
                <p className="text-3xl font-bold text-white">{stats.active_policies.toLocaleString()}</p>
                <p className="text-green-400 text-sm font-bold mb-1">↑{stats.active_policies_change}%</p>
              </div>
            </div>
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl">
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Active Claims Today</p>
              <div className="flex items-end gap-3">
                <p className="text-3xl font-bold text-white">{stats.claims_today}</p>
              </div>
            </div>
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl">
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Total Payouts This Week</p>
              <div className="flex items-end gap-3">
                <p className="text-3xl font-bold text-white font-mono">₹{stats.payouts_this_week.toLocaleString()}</p>
              </div>
            </div>
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl relative overflow-hidden">
               <div className={`absolute right-0 top-0 bottom-0 w-2 ${stats.loss_ratio > 80 ? 'bg-red-500' : 'bg-green-500'}`}></div>
              <p className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-1">Loss Ratio</p>
              <div className="flex items-end gap-3">
                <p className="text-3xl font-bold text-white">{stats.loss_ratio}%</p>
                <p className={`text-sm font-bold mb-1 ${stats.loss_ratio > 80 ? 'text-red-400' : 'text-green-400'}`}>
                  {stats.loss_ratio > 80 ? '(Warning)' : '(Healthy)'}
                </p>
              </div>
            </div>
          </div>

          {/* CHARTS ROW */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* TRIGGER EVENTS - BAR CHART */}
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl col-span-1 border-t-2 border-t-orange-500">
              <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4">Trigger Events This Week</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stats.trigger_events_this_week} margin={{ top: 5, right: 5, left: -25, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="type" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false}/>
                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false}/>
                    <Tooltip content={<DarkTooltip />} cursor={{fill: '#334155', opacity: 0.4}}/>
                    <Bar dataKey="count" fill="#f97316" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* PREMIUM VS PAYOUTS - AREA CHART */}
            <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl col-span-1 lg:col-span-2">
              <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4">Premium vs Payouts (12W)</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={trends} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorPremiums" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#22c55e" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorPayouts" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                    <XAxis dataKey="week" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false}/>
                    <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `₹${val/1000}k`}/>
                    <Tooltip content={<DarkTooltip />} />
                    <Area type="monotone" dataKey="premiums" stroke="#22c55e" strokeWidth={3} fillOpacity={1} fill="url(#colorPremiums)" />
                    <Area type="monotone" dataKey="payouts" stroke="#ef4444" strokeWidth={3} fillOpacity={1} fill="url(#colorPayouts)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
            
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
             {/* DONUT CHART */}
             <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl flex flex-col items-center justify-center">
               <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4 w-full">Claims Breakdown</h3>
               <div className="h-48 w-full relative">
                 <ResponsiveContainer width="100%" height="100%">
                   <PieChart>
                     <Pie
                       data={donutData}
                       cx="50%" cy="50%"
                       innerRadius={60} outerRadius={80}
                       paddingAngle={5}
                       dataKey="value"
                     >
                       {donutData.map((entry, index) => (
                         <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                       ))}
                     </Pie>
                     <Tooltip content={<DarkTooltip />} />
                   </PieChart>
                 </ResponsiveContainer>
                 <div className="absolute inset-0 flex items-center justify-center flex-col pointer-events-none">
                    <span className="text-2xl font-bold text-white">
                      {Math.round((stats.claims_by_status.auto_approved / (stats.claims_by_status.auto_approved+stats.claims_by_status.flagged+stats.claims_by_status.rejected+stats.claims_by_status.held || 1))*100)}%
                    </span>
                    <span className="text-[10px] text-slate-400 uppercase">Auto-Apprv</span>
                 </div>
               </div>
               <div className="flex gap-4 mt-4 text-xs font-semibold text-slate-400">
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#22c55e]"></span> Auto</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#f59e0b]"></span> Flagged</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#3b82f6]"></span> Held</div>
                  <div className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#ef4444]"></span> Rejected</div>
               </div>
             </div>

             {/* ZONE HEATMAP TABLE */}
             <div className="bg-[#1e293b] border border-slate-800 p-5 rounded-xl col-span-1 lg:col-span-2 overflow-hidden flex flex-col">
               <h3 className="text-white text-sm font-bold uppercase tracking-wider mb-4">Zone Risk Heatmap</h3>
               <div className="flex-1 overflow-x-auto">
                 <table className="w-full text-left text-sm whitespace-nowrap">
                   <thead>
                     <tr className="text-slate-400 border-b border-slate-700">
                       <th className="pb-3 font-semibold">Zone</th>
                       <th className="pb-3 font-semibold text-right">Policies</th>
                       <th className="pb-3 font-semibold text-right">Claims (7d)</th>
                       <th className="pb-3 font-semibold text-right">Loss Ratio</th>
                       <th className="pb-3 font-semibold">Risk Level</th>
                     </tr>
                   </thead>
                   <tbody>
                     {stats.zone_summary.map((zone, idx) => (
                       <tr key={idx} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors">
                         <td className="py-3 font-bold text-white">{zone.zone}</td>
                         <td className="py-3 text-right font-mono">{zone.active_policies}</td>
                         <td className="py-3 text-right font-mono">{zone.claims_this_week}</td>
                         <td className="py-3 text-right font-mono text-orange-400">{zone.loss_ratio}%</td>
                         <td className="py-3">
                           <span className={`px-2 py-1 rounded-md text-[10px] font-bold uppercase tracking-wider ${
                             zone.risk === 'high' ? 'bg-red-500/20 text-red-500 border border-red-500/20' : 
                             zone.risk === 'medium' ? 'bg-yellow-500/20 text-yellow-500 border border-yellow-500/20' :
                             'bg-green-500/20 text-green-500 border border-green-500/20'
                           }`}>
                             {zone.risk}
                           </span>
                         </td>
                       </tr>
                     ))}
                   </tbody>
                 </table>
               </div>
             </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pb-20">
             
             {/* PREDICTIVE AI SHOWPIECE */}
             <div className="bg-gradient-to-br from-indigo-900 via-[#1e293b] to-[#1e293b] border border-indigo-500/30 p-6 rounded-xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none"><Cpu size={120}/></div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-white text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                    <Zap className="text-yellow-400" size={16}/> {predictions.title}
                  </h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 animate-pulse">AI ACTIVE</span>
                </div>
                
                <p className="text-slate-300 text-sm mb-3">{predictions.intro}</p>
                <ul className="space-y-2 mb-6">
                  {predictions.bullets.map((b, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                      <div className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0"></div>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                   <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-semibold text-slate-400">Recommended Reserve</span>
                      <span className="font-mono text-lg font-bold text-white">₹{predictions.reserve.toLocaleString()}</span>
                   </div>
                   <div className="flex justify-between items-center">
                      <span className="text-sm font-semibold text-slate-400">Suggested Adjustment</span>
                      <span className="text-sm font-bold text-orange-400">{predictions.premium_adjustment}</span>
                   </div>
                </div>
             </div>

             {/* FRAUD ALERTS SECTION */}
             <div className="bg-[#1e293b] border border-slate-800 rounded-xl overflow-hidden flex flex-col">
                <div className="p-5 border-b border-slate-800 flex justify-between items-center">
                   <h3 className="text-white text-sm font-bold uppercase tracking-wider flex items-center gap-2">
                     <ShieldAlert className="text-red-500" size={16}/> Fraud & Review Queue
                   </h3>
                   <span className="bg-red-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">{fraudAlerts.length} pending</span>
                </div>
                <div className="flex-1 overflow-y-auto max-h-[300px]">
                   {fraudAlerts.map((alert, idx) => (
                     <div key={idx} className="p-4 border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors flex justify-between items-center group">
                        <div>
                          <p className="text-white text-sm font-bold">{alert.user} <span className="text-slate-500 font-mono text-xs ml-2">{alert.id}</span></p>
                          <p className="text-slate-400 text-xs mt-1">{alert.reason}</p>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right hidden sm:block">
                            <p className="font-mono text-white text-sm">₹{alert.amount}</p>
                            <p className="text-[10px] font-bold text-red-400 uppercase mt-0.5">Score: {alert.fraud_score}</p>
                          </div>
                          <button className="bg-slate-700 hover:bg-slate-600 text-white text-xs font-bold px-3 py-1.5 rounded-md transition-colors opacity-0 group-hover:opacity-100">
                            Review
                          </button>
                        </div>
                     </div>
                   ))}
                </div>
             </div>
          </div>

          {/* DEMO CONTROLS (God Mode) */}
          <div className="bg-[#0f172a] border-2 border-dashed border-red-500/40 p-6 rounded-xl relative overflow-hidden mb-12">
             <div className="absolute top-0 right-0 bg-red-500 text-white text-[10px] font-bold uppercase px-3 py-1 rounded-bl-lg">Simulator Mode</div>
             
             <div className="mb-4">
               <h3 className="text-white text-base font-bold flex items-center gap-2 font-mono">
                 <AlertTriangle className="text-red-500" /> GOD MODE: FORCE TRIGGER
               </h3>
               <p className="text-slate-500 text-xs mt-1">Inject weather events directly into the parametric engine to instantly evaluate and disburse funds to affected grid workers.</p>
             </div>

             <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">City</label>
                  <select value={demoZone} onChange={(e) => setDemoZone(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500">
                    <option value="Mumbai">Mumbai</option>
                    <option value="Delhi">Delhi</option>
                    <option value="Bengaluru">Bengaluru</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Sub Zone</label>
                  <input type="text" value={demoSubZone} onChange={(e) => setDemoSubZone(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Trigger Type</label>
                  <select value={demoTriggerType} onChange={(e) => setDemoTriggerType(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500">
                    <option value="heavy_rain">Heavy Rain</option>
                    <option value="moderate_rain">Moderate Rain</option>
                    <option value="severe_aqi">Severe AQI</option>
                    <option value="extreme_heat">Extreme Heat</option>
                    <option value="flood_warning">Flood Warning</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-400 uppercase mb-1">Value (e.g. mm, temp)</label>
                  <input type="number" value={demoValue} onChange={(e) => setDemoValue(e.target.value)} className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500" />
                </div>
             </div>

             <div className="flex gap-4 items-stretch">
               <button 
                 onClick={handleSimulate}
                 disabled={simulating}
                 className="bg-red-600 hover:bg-red-700 text-white font-extrabold px-8 py-3 rounded-xl transition-colors shrink-0 disabled:opacity-50"
               >
                 {simulating ? 'FIRING...' : '🔥 FIRE TRIGGER'}
               </button>
               
               <div className="bg-black/50 border border-slate-800 rounded-xl p-3 flex-1 overflow-y-auto font-mono text-xs text-green-400 max-h-32">
                 {simulateLog.length === 0 ? (
                   <span className="text-slate-600">Simulator ready... awaiting payload.</span>
                 ) : (
                   simulateLog.map((log, i) => <div key={i}>{log}</div>)
                 )}
               </div>
             </div>
          </div>

            </>
          )}
        </div>
      </div>
    </div>
  );
}
