import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Settings, Home, FileText, Zap, User, 
  Droplet, ThermometerSun, Wind, ArrowUpRight, ArrowDownRight,
  MapPin, Shield, AlertTriangle, CloudRain, Bell
} from 'lucide-react';
import api from '../api/client';

export default function Dashboard() {
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [profile, setProfile] = useState(null);
  const [policy, setPolicy] = useState(null);
  const [triggers, setTriggers] = useState(null);
  const [claims, setClaims] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/register');
      return;
    }

    // Set authorization header globally for all subsequent requests
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    const loadDashboardData = async () => {
      try {
        const [profileRes, policyRes, triggersRes, claimsRes] = await Promise.all([
          api.get('/auth/profile'),
          api.get('/policy/active').catch(() => ({ data: null })), // If no policy, it throws 404
          api.get('/triggers/active').catch(() => ({ data: null })),
          api.get('/v1/claims/my-claims?limit=5').catch(() => ({ data: [] }))
        ]);

        setProfile(profileRes.data);
        setPolicy(policyRes.data);
        setTriggers(triggersRes.data);
        setClaims(claimsRes.data || []);
      } catch (err) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          localStorage.removeItem('access_token');
          navigate('/register');
        }
        console.error("Dashboard data load error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
          <Shield className="text-secondary w-12 h-12" />
        </motion.div>
      </div>
    );
  }

  // Activity stats
  const premiumPaid = profile?.active_policy?.weekly_premium || 0; // Or fetch from history
  const activeNetBenefit = profile?.stats?.net_benefit_inr || 0; 
  const isNetPositive = activeNetBenefit >= 0;

  // Animation variants
  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 300, damping: 24 } } };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans pb-24 text-gray-900 border-x border-gray-200 mx-auto w-full max-w-md relative shadow-2xl overflow-x-hidden">
      
      <motion.div variants={containerVariants} initial="hidden" animate="visible" className="flex-1 overflow-y-auto px-5 pt-6 relative space-y-7 z-10">
        
        {/* TOP BAR */}
        <motion.div variants={itemVariants} className="flex justify-between items-center bg-white p-3 rounded-2xl shadow-sm border border-gray-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center border-2 border-white shadow-sm font-bold text-primary">
              {profile?.name?.charAt(0) || 'U'}
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">Hey, {profile?.name?.split(' ')[0] || 'Rider'} 👋</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className={`w-2 h-2 rounded-full ${policy ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)] animate-pulse' : 'bg-red-500'}`}></span>
                <span className="text-xs font-bold text-secondary tracking-wide uppercase">{policy ? 'Protected' : 'Unprotected'}</span>
              </div>
            </div>
          </div>
          <button className="p-2 text-gray-400 hover:bg-gray-50 hover:text-gray-600 rounded-full transition-colors relative">
            <Bell size={20} strokeWidth={2.5} />
            {claims.length > 0 && <span className="absolute top-2 right-2.5 w-2 h-2 bg-red-500 rounded-full border border-white"></span>}
          </button>
        </motion.div>

        {/* HERO COVERAGE CARD */}
        <motion.div variants={itemVariants} className="relative w-full aspect-[1.7] rounded-3xl overflow-hidden shadow-lg border border-gray-200 flex flex-col">
          {policy ? (
            <div className="absolute inset-0 bg-gradient-to-br from-green-600 via-emerald-700 to-green-900 grid place-items-center">
               {/* Pattern overlay */}
               <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)', backgroundSize: '16px 16px' }}></div>
            </div>
          ) : (
             <div className="absolute inset-0 bg-gradient-to-br from-gray-500 to-gray-700"></div>
          )}

          <div className="relative z-10 p-6 flex flex-col h-full text-white">
            <div className="flex justify-between items-start mb-auto">
              <div>
                <span className="bg-white/20 backdrop-blur-md px-3 py-1 rounded-full text-xs font-bold tracking-wider uppercase border border-white/10 shadow-sm">
                  {policy ? `${policy.tier} Plan ✅` : 'No Active Plan ⚠️'}
                </span>
                <p className="mt-3 text-3xl font-extrabold tracking-tight drop-shadow-sm">
                  {policy ? `₹${parseInt(policy.max_payout_per_event)}` : '₹0'}
                </p>
                <p className="text-white/80 font-medium text-sm mt-0.5 font-mono">max payout per event</p>
              </div>
              <Shield size={36} className="text-white/20" strokeWidth={1}/>
            </div>

            <div className="mt-auto border-t border-white/20 pt-4 flex justify-between items-end">
              <div>
                 <p className="text-xs text-white/70 font-medium uppercase tracking-wider mb-1">Covers Until</p>
                 <p className="font-bold text-sm bg-black/20 px-2.5 py-1 rounded-md w-fit backdrop-blur-sm">
                   {policy ? new Date(policy.end_date).toLocaleDateString('en-GB', {weekday: 'long', month: 'short', day: 'numeric'}) : '--'}
                 </p>
              </div>
              <div className="text-right">
                <p className="text-xs text-white/70 font-medium uppercase tracking-wider mb-1">Events Left</p>
                <p className="font-extrabold text-xl font-mono">{policy ? policy.events_remaining : 0}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {!policy && (
           <motion.div variants={itemVariants} className="flex justify-center -mt-4 relative z-20">
             <button className="bg-primary hover:bg-orange-600 w-11/12 py-3.5 rounded-2xl text-white font-bold tracking-wide shadow-lg shadow-orange-500/30 flex justify-center items-center gap-2 transition-all">
               Get Covered Now <ArrowUpRight size={18} strokeWidth={3}/>
             </button>
           </motion.div>
        )}

        {/* LIVE WEATHER STRIP */}
        <motion.div variants={itemVariants} className="w-full">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest flex items-center gap-1.5"><MapPin size={14} className="text-primary"/> {profile?.sub_zone} Conditions</h2>
            <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-bold border border-blue-100 flex items-center gap-1"><span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-ping"></span>Live</span>
          </div>
          
          <div className="flex gap-3 overflow-x-auto pb-4 scrollbar-hide snap-x">
            {/* RAIN */}
            <div className={`snap-center shrink-0 w-36 p-4 rounded-2xl border ${triggers?.any_payout_active ? 'bg-red-50 border-red-200 animate-pulse' : 'bg-white border-gray-100'} shadow-sm flex flex-col`}>
              <div className="flex justify-between items-start mb-2">
                <Droplet size={20} className={triggers?.any_payout_active ? 'text-red-500' : 'text-blue-500'} strokeWidth={2.5}/>
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${triggers?.any_payout_active ? 'bg-red-100 text-red-700' : 'bg-green-50 text-green-700'}`}>
                  {triggers?.any_payout_active ? 'Trigger' : 'Safe'}
                </span>
              </div>
              <p className="text-2xl font-extrabold text-secondary mt-1">{triggers?.current_conditions?.weather?.rain_mm_3hr || 0}<span className="text-sm font-semibold text-gray-400">mm</span></p>
              <p className="text-xs text-gray-500 font-medium mt-1 uppercase tracking-wider">3hr Rain</p>
            </div>

            {/* TEMP */}
            <div className="snap-center shrink-0 w-36 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-2">
                <ThermometerSun size={20} className="text-orange-500" strokeWidth={2.5}/>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-green-50 text-green-700">Safe</span>
              </div>
              <p className="text-2xl font-extrabold text-secondary mt-1 tracking-tight">{triggers?.current_conditions?.weather?.temp_c || 28}°</p>
              <p className="text-xs text-gray-500 font-medium mt-1 uppercase tracking-wider">Temp</p>
            </div>

            {/* AQI */}
            <div className="snap-center shrink-0 w-36 p-4 rounded-2xl bg-white border border-gray-100 shadow-sm flex flex-col">
              <div className="flex justify-between items-start mb-2">
                <Wind size={20} className="text-slate-500" strokeWidth={2.5}/>
                <span className="text-xs font-bold px-2 py-0.5 rounded bg-yellow-50 text-yellow-700">{triggers?.current_conditions?.aqi?.category || 'Mod'}</span>
              </div>
              <p className="text-2xl font-extrabold text-secondary mt-1 tracking-tight">{triggers?.current_conditions?.aqi?.aqi || 120}</p>
              <p className="text-xs text-gray-500 font-medium mt-1 uppercase tracking-wider">AQI Index</p>
            </div>
          </div>
        </motion.div>

        {/* THIS WEEK'S ACTIVITY */}
        <motion.div variants={itemVariants} className="bg-white p-5 rounded-2xl border border-gray-100 shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-gray-50 rounded-full -mr-10 -mt-10 opacity-70 border border-gray-100"></div>
          <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest mb-4 relative z-10">This Week's Activity</h2>
          
          <div className="grid grid-cols-2 gap-y-5 gap-x-4 relative z-10">
            <div>
              <p className="text-xs text-gray-500 font-medium">Premium Paid</p>
              <p className="text-lg font-bold text-secondary mt-0.5 flex items-center gap-1"><ArrowDownRight size={16} className="text-gray-400"/> ₹{premiumPaid}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Events Triggered</p>
              <p className="text-lg font-bold text-secondary mt-0.5">{profile?.stats?.total_claims || 0}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Payouts Received</p>
              <p className="text-lg font-bold text-secondary mt-0.5 flex items-center gap-1"><ArrowUpRight size={16} className="text-green-500"/> ₹{profile?.stats?.total_payouts_inr || 0}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 font-medium">Net Benefit</p>
              <p className={`text-lg font-bold mt-0.5 px-2 py-0.5 rounded w-fit ${isNetPositive ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'}`}>
                {isNetPositive ? '+' : ''}₹{activeNetBenefit}
              </p>
            </div>
          </div>
        </motion.div>

        {/* RECENT PAYOUTS TIMELINE */}
        <motion.div variants={itemVariants} className="pb-8">
          <div className="flex justify-between items-center mb-4">
             <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest">Recent Payouts</h2>
             <span className="text-xs text-primary font-bold cursor-pointer hover:underline">View All</span>
          </div>

          <div className="space-y-4">
            {claims.length > 0 ? claims.map((claim) => (
              <div key={claim.id} className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex items-start gap-4 active:scale-95 transition-transform cursor-pointer">
                <div className="w-12 h-12 bg-green-50 rounded-xl flex items-center justify-center border border-green-100 shrink-0">
                  <CloudRain size={24} className="text-green-600" strokeWidth={2} />
                </div>
                <div className="flex-1 w-full overflow-hidden">
                  <div className="flex justify-between items-start w-full">
                    <p className="font-bold text-gray-800 text-base truncate pr-2 w-full">{(claim.trigger_type || 'Unknown').replace('_', ' ').toUpperCase()}</p>
                    <p className="font-extrabold text-green-600 text-base shrink-0">₹{parseInt(claim.payout_amount)}</p>
                  </div>
                  <p className="text-xs text-gray-500 font-medium mt-1 flex items-center justify-between">
                    <span>{new Date(claim.initiated_at).toLocaleDateString()}</span>
                    {(claim.status === 'auto_approved' || claim.status === 'paid') ? (
                       <span className="text-[10px] bg-green-50 text-green-700 px-2 py-0.5 rounded-full font-bold border border-green-100 uppercase tracking-wide">Auto-Apprv ✅</span>
                    ) : (
                       <span className="text-[10px] bg-amber-50 text-amber-700 px-2 py-0.5 rounded-full font-bold border border-amber-100 uppercase tracking-wide">{claim.status}</span>
                    )}
                  </p>
                  <p className="text-[10px] text-gray-400 mt-2 font-mono bg-gray-50 px-2 py-1 rounded inline-block">Fraud Score: {claim.fraud_score}/100</p>
                </div>
              </div>
            )) : (
              <div className="text-center py-8 bg-white rounded-2xl border border-gray-200 border-dashed">
                <FileText size={32} className="mx-auto text-gray-300 mb-2"/>
                <p className="text-gray-500 font-medium text-sm">No recent claims.</p>
                <p className="text-xs text-gray-400 mt-1">You're safe for now!</p>
              </div>
            )}
          </div>
        </motion.div>

      </motion.div>

       {/* FLOATING RENEW BUTTON */}
       {policy && (
         <div className="fixed bottom-24 left-0 right-0 max-w-md mx-auto px-5 z-20">
            <button className="w-full bg-secondary text-white py-4 rounded-2xl font-extrabold shadow-[0_10px_25px_-5px_rgba(27,42,74,0.4)] flex justify-between items-center px-6 active:scale-95 transition-transform hover:bg-slate-800 border border-slate-700">
              <span className="flex items-center gap-2 tracking-wide"><Shield size={18} strokeWidth={2.5}/> Renew Cover</span>
              <span className="font-mono text-lg tracking-tighter">₹138 <span className="text-xs text-slate-400 font-sans tracking-normal font-medium">/wk</span></span>
            </button>
         </div>
       )}

      {/* BOTTOM NAVIGATION */}
      <div className="fixed bottom-0 left-0 right-0 w-full max-w-md mx-auto bg-white border-t border-gray-100 pb-safe pt-3 px-6 flex justify-between items-center z-30 pb-5 shadow-[0_-10px_15px_-3px_rgba(0,0,0,0.02)]">
        <Link to="/" className="flex flex-col items-center gap-1 cursor-pointer group">
          <div className="bg-primary/10 p-2 rounded-xl group-hover:bg-primary/20 transition-colors">
            <Home className="text-primary w-6 h-6" strokeWidth={2.5}/>
          </div>
          <span className="text-[10px] font-bold text-primary">Home</span>
        </Link>
        <Link to="/policy" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <Shield className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Policy</span>
        </Link>
        <Link to="/claims" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <Zap className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Triggers</span>
        </Link>
        <Link to="#" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <User className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Profile</span>
        </Link>
      </div>
    </div>
  );
}
