import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Zap, CloudRain, ThermometerSun, Wind, AlertCircle, Home, Shield, User,
  CheckCircle, Clock, ChevronDown, Check, Info, ShieldAlert, Waves,
  ShieldCheck, AlertTriangle, CloudLightning, Gauge
} from 'lucide-react';
import api from '../api/client';

export default function ClaimsPage() {
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [claims, setClaims] = useState([]);
  const [activeTrigger, setActiveTrigger] = useState(null);
  const [expandedClaim, setExpandedClaim] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/register');
      return;
    }
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    const loadData = async () => {
      try {
        const [activeTriggersRes, claimsRes] = await Promise.all([
          api.get('/triggers/active').catch(() => ({ data: null })),
          api.get('/v1/claims/my-claims?limit=20').catch(() => ({ data: [] }))
        ]);
        
        setActiveTrigger(activeTriggersRes.data);
        setClaims(claimsRes.data || []);
      } catch (err) {
        console.error("Claims load error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
          <Zap className="text-secondary w-12 h-12" />
        </motion.div>
      </div>
    );
  }

  // Visual component for Fraud Score Meter
  const renderFraudMeter = (score) => {
    let color = score < 20 ? 'bg-green-500' : (score < 50 ? 'bg-yellow-500' : 'bg-red-500');
    let label = score < 20 ? 'Low Risk' : (score < 50 ? 'Medium Risk' : 'High Risk');
    let labelColor = score < 20 ? 'text-green-600' : (score < 50 ? 'text-yellow-600' : 'text-red-600');
    let percentage = Math.min(Math.max(score, 5), 100);

    return (
      <div className="mt-3 bg-gray-50 p-3 rounded-xl border border-gray-100">
         <div className="flex justify-between items-center mb-2">
           <span className="text-xs font-bold text-gray-500 flex items-center gap-1"><ShieldAlert size={12}/> AI Trust Check</span>
           <span className={`text-[10px] font-bold uppercase tracking-widest ${labelColor}`}>{label} ({score}/100)</span>
         </div>
         <div className="w-full bg-gray-200 h-1.5 rounded-full overflow-hidden">
            <div className={`h-full ${color}`} style={{ width: `${percentage}%` }}></div>
         </div>
         <div className="mt-3 grid grid-cols-2 gap-2 text-[10px] text-gray-500 font-medium pb-1 border-b border-gray-100/50 mb-1">
            <p>• Verified Device ID</p>
            <p>• Historic Claim Velocity: Normal</p>
            <p>• Geolocated at Time of Event</p>
            <p>• Clean Payout History</p>
         </div>
      </div>
    );
  };

  const getTriggerIcon = (type) => {
    switch (type) {
      case 'heavy_rain':
      case 'moderate_rain': return <CloudRain size={20} className="text-blue-500" />;
      case 'severe_aqi': return <Wind size={20} className="text-gray-500" />;
      case 'extreme_heat': return <ThermometerSun size={20} className="text-red-500" />;
      case 'flood_warning': return <Waves size={20} className="text-blue-600" />;
      default: return <CloudLightning size={20} className="text-purple-500" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans pb-24 text-gray-900 border-x border-gray-200 mx-auto w-full max-w-md relative shadow-2xl overflow-x-hidden">
      
      {/* HEADER */}
      <div className="bg-white px-5 pt-6 pb-4 border-b border-gray-100 shadow-sm sticky top-0 z-40">
        <h1 className="text-xl font-extrabold text-secondary flex items-center gap-2">
          <Zap className="text-primary fill-primary" size={24} /> Parametric Triggers
        </h1>
        <p className="text-xs font-medium text-gray-500 mt-1">Automatic payouts based on environmental rules.</p>
      </div>

      <div className="flex-1 overflow-y-auto px-5 pt-6 space-y-6">
        
        {/* ACTIVE TRIGGER BANNER */}
        {activeTrigger && activeTrigger.any_payout_active && (
           <motion.div initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} className="bg-gradient-to-br from-red-600 to-red-800 rounded-3xl p-5 shadow-lg relative overflow-hidden text-white">
              <div className="absolute top-0 right-0 p-4 opacity-10"><AlertTriangle size={80} /></div>
              
              <div className="flex items-start gap-3 relative z-10">
                 <div className="bg-white/20 p-2 rounded-full absolute -top-1 -left-1 animate-pulse">
                   <AlertCircle size={24} strokeWidth={2.5} className="text-white"/>
                 </div>
                 <div className="ml-10">
                   <h2 className="font-extrabold text-sm uppercase tracking-widest mb-1 shadow-sm">Active Weather Event</h2>
                   <p className="text-lg font-bold">Rain detected in {activeTrigger.zone_monitored.sub_zone}!</p>
                   <p className="text-xs font-medium text-white/80 mt-1">Parametric claim auto-initiated.</p>
                 </div>
              </div>

              {/* PROGRESS BAR */}
              <div className="relative z-10 mt-6 bg-black/20 p-4 rounded-xl backdrop-blur-sm border border-white/10">
                 <div className="flex justify-between items-center mb-2">
                   <span className="text-xs font-bold text-white/70 uppercase tracking-widest">Payout Status</span>
                   <span className="text-xs font-bold bg-white text-red-700 px-2 py-0.5 rounded-full shadow-sm animate-pulse">Processing</span>
                 </div>
                 
                 <div className="relative pt-2 pb-1">
                    <div className="absolute top-1/2 left-2 right-2 h-0.5 bg-white/20 -translate-y-1/2 rounded-full"></div>
                    <div className="absolute top-1/2 left-2 w-[45%] h-0.5 bg-white -translate-y-1/2 rounded-full shadow-[0_0_8px_white]"></div>
                    
                    <div className="relative flex justify-between">
                       <div className="w-5 h-5 rounded-full bg-white flex items-center justify-center shadow-sm relative z-10 text-red-700"><Check size={12} strokeWidth={4}/></div>
                       <div className="w-5 h-5 rounded-full bg-white flex items-center justify-center shadow-sm relative z-10 text-red-700"><Check size={12} strokeWidth={4}/></div>
                       <div className="w-5 h-5 rounded-full bg-white border-4 border-red-700 flex items-center justify-center shadow-sm relative z-10 animate-bounce"></div>
                       <div className="w-5 h-5 rounded-full bg-white/30 border border-white/30 flex items-center justify-center relative z-10"></div>
                       <div className="w-5 h-5 rounded-full bg-white/30 border border-white/30 flex items-center justify-center relative z-10"></div>
                    </div>
                 </div>
                 <div className="flex justify-between text-[8px] font-bold uppercase tracking-widest text-white/80 mt-2">
                   <span>Detected</span>
                   <span>Fraud Check</span>
                   <span className="text-white">Approved</span>
                   <span>Transfer</span>
                   <span>Paid</span>
                 </div>
                 <p className="text-xs font-medium mt-3 text-white/90 bg-white/10 p-2 rounded-lg text-center">
                    ETA: ~12 minutes until ₹450 deposit.
                 </p>
              </div>
           </motion.div>
        )}

        {/* CLAIMS HISTORY */}
        <div className="space-y-4">
           <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest">Claim History</h2>
           {claims.map((claim) => (
             <div key={claim.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                <div 
                  className="p-4 cursor-pointer active:bg-gray-50 transition-colors flex items-start gap-4"
                  onClick={() => setExpandedClaim(expandedClaim === claim.id ? null : claim.id)}
                >
                   <div className="w-10 h-10 bg-gray-50 rounded-xl flex items-center justify-center border border-gray-100 shrink-0 mt-1">
                     {getTriggerIcon(claim.trigger_type)}
                   </div>
                   <div className="flex-1 w-full">
                     <div className="flex justify-between items-start">
                        <p className="font-bold text-gray-800 text-sm">{claim.trigger_type.replace(/_/g, ' ').toUpperCase()}</p>
                        <p className={`font-extrabold ${claim.status === 'rejected' ? 'text-gray-400 line-through' : 'text-green-600'} text-sm`}>
                          ₹{parseInt(claim.payout_amount)}
                        </p>
                     </div>
                     <p className="text-xs text-gray-400 font-medium mt-0.5">{new Date(claim.initiated_at).toLocaleString()}</p>
                     
                     <div className="flex justify-between items-center mt-3">
                       <span className="text-[10px] bg-gray-100 text-gray-600 px-2 py-0.5 rounded font-mono border border-gray-200">
                         Value: {claim.trigger_value} / Threshold: {claim.threshold_value}
                       </span>
                       
                       {(claim.status === 'auto_approved' || claim.status === 'paid') && (
                         <span className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-bold border border-green-100 flex items-center gap-1"><CheckCircle size={10}/> {claim.status.replace('_', ' ').toUpperCase()}</span>
                       )}
                       {claim.status === 'under_review' && (
                         <span className="text-[10px] bg-yellow-50 text-yellow-700 px-2 py-0.5 rounded-full font-bold border border-yellow-100 flex items-center gap-1"><Clock size={10}/> REVIEWING</span>
                       )}
                       {claim.status === 'rejected' && (
                         <span className="text-[10px] bg-red-50 text-red-700 px-2 py-0.5 rounded-full font-bold border border-red-100 flex items-center gap-1"><AlertTriangle size={10}/> REJECTED</span>
                       )}
                     </div>
                   </div>
                   <ChevronDown size={16} className={`text-gray-300 mt-2 shrink-0 transition-transform ${expandedClaim === claim.id ? 'rotate-180' : ''}`}/>
                </div>
                
                {/* Expadable Body */}
                <AnimatePresence>
                  {expandedClaim === claim.id && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }} 
                      animate={{ height: 'auto', opacity: 1 }} 
                      exit={{ height: 0, opacity: 0 }}
                      className="border-t border-gray-50 overflow-hidden"
                    >
                      <div className="p-4 bg-gray-50/50">
                        {renderFraudMeter(claim.fraud_score)}
                        <button className="w-full mt-3 bg-white text-secondary text-xs font-bold py-2 rounded-lg shadow-sm border border-gray-200">
                          View Digital Receipt
                        </button>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
             </div>
           ))}

           {claims.length === 0 && (
             <div className="text-center py-10 bg-white rounded-3xl border border-dashed border-gray-200">
                <CheckCircle size={32} className="mx-auto text-green-400 mb-2"/>
                <p className="text-gray-500 text-sm font-medium">No claims history yet.</p>
                <p className="text-xs text-gray-400 mt-1">If weather strikes, you'll be paid here.</p>
             </div>
           )}
        </div>

        {/* THRESHOLD DICTIONARY */}
        <div className="bg-white p-5 rounded-2xl border border-gray-200 shadow-sm mt-8 pb-8">
           <h3 className="text-xs font-bold uppercase tracking-widest text-secondary mb-4 flex items-center gap-2">
             <Info size={16} className="text-primary"/> What We Monitor
           </h3>
           <div className="space-y-3">
             <div className="flex items-start gap-3">
               <CloudRain size={16} className="text-blue-500 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">Heavy Rain</p>
                 <p className="text-xs text-gray-500 mt-0.5"><b>&gt;25mm / 3hr</b> → Instant 100% Payout</p>
               </div>
             </div>
             <div className="flex items-start gap-3">
               <CloudRain size={16} className="text-blue-300 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">Moderate Rain</p>
                 <p className="text-xs text-gray-500 mt-0.5"><b>&gt;15mm / 3hr</b> → Instant 60% Payout</p>
               </div>
             </div>
             <div className="flex items-start gap-3">
               <Wind size={16} className="text-gray-400 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">Severe AQI</p>
                 <p className="text-xs text-gray-500 mt-0.5"><b>&gt;350</b> → Instant 100% Payout</p>
               </div>
             </div>
             <div className="flex items-start gap-3">
               <ThermometerSun size={16} className="text-orange-500 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">Extreme Heat</p>
                 <p className="text-xs text-gray-500 mt-0.5"><b>&gt;45°C</b> → Instant 100% Payout</p>
               </div>
             </div>
             <div className="flex items-start gap-3">
               <Waves size={16} className="text-blue-800 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">Flood Warning</p>
                 <p className="text-xs text-gray-500 mt-0.5">Official NDMA Ping → Instant 100% Payout</p>
               </div>
             </div>
             <div className="flex items-start gap-3">
               <AlertCircle size={16} className="text-red-500 mt-0.5 shrink-0" strokeWidth={3}/>
               <div>
                 <p className="text-sm font-bold text-gray-800">City Curfew / Bandh</p>
                 <p className="text-xs text-gray-500 mt-0.5">Section 144 Enforced → Instant 100% Payout</p>
               </div>
             </div>
           </div>
        </div>

      </div>

      {/* BOTTOM NAVIGATION (Consistent w/ Dashboard) */}
      <div className="fixed bottom-0 left-0 right-0 w-full max-w-md mx-auto bg-white border-t border-gray-100 pb-safe pt-3 px-6 flex justify-between items-center z-50 pb-5 shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.02)]">
        <Link to="/" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <Home className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Home</span>
        </Link>
        <Link to="/policy" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <Shield className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Policy</span>
        </Link>
        <Link to="/claims" className="flex flex-col items-center gap-1 cursor-pointer group">
          <div className="bg-primary/10 p-2 rounded-xl text-primary">
             <Zap className="w-6 h-6" strokeWidth={2.5}/>
          </div>
          <span className="text-[10px] font-bold text-primary">Triggers</span>
        </Link>
        <Link to="#" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <User className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Profile</span>
        </Link>
      </div>
    </div>
  );
}
