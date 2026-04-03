import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Shield, Check, Clock, Info, CheckCircle, ChevronRight,
  TrendingUp, TrendingDown, Minus, Home, Zap, User, Star
} from 'lucide-react';
import api from '../api/client';

export default function PolicyPage() {
  const navigate = useNavigate();
  
  const [activeTab, setActiveTab] = useState('purchase');
  const [loading, setLoading] = useState(true);
  const [tiersData, setTiersData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [selectedTierKey, setSelectedTierKey] = useState('standard');
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/register');
      return;
    }
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;

    const loadData = async () => {
      try {
        const [tiersRes, historyRes] = await Promise.all([
          api.get('/premium/all-tiers'),
          api.get('/policy/history?weeks=12')
        ]);
        setTiersData(tiersRes.data);
        setHistoryData(historyRes.data);
      } catch (err) {
        if (err.response?.status === 401 || err.response?.status === 403) {
          localStorage.removeItem('access_token');
          navigate('/register');
        }
        console.error("Policy data load error:", err);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [navigate]);

  const handlePurchase = async () => {
    setProcessing(true);
    try {
      await api.post('/policy/create', { tier: selectedTierKey });
      navigate('/');
    } catch (err) {
      alert(err.response?.data?.detail?.message || "Purchase failed");
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
          <Shield className="text-secondary w-12 h-12" />
        </motion.div>
      </div>
    );
  }

  const selectedTierData = tiersData?.tiers?.find(t => t.tier === selectedTierKey);

  // Animation variants
  const containerVariants = { hidden: { opacity: 0 }, visible: { opacity: 1, transition: { staggerChildren: 0.1 } } };
  const itemVariants = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col font-sans pb-24 text-gray-900 border-x border-gray-200 mx-auto w-full max-w-md relative shadow-2xl overflow-x-hidden">
      
      {/* HEADER & TABS */}
      <div className="bg-white px-5 pt-6 pb-2 border-b border-gray-100 shadow-sm sticky top-0 z-40">
        <h1 className="text-xl font-extrabold text-secondary flex items-center gap-2 mb-4">
          <Shield className="text-primary" size={24} /> Policy
        </h1>
        
        <div className="flex bg-gray-100 p-1 rounded-xl w-full">
          <button 
            onClick={() => setActiveTab('purchase')}
            className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${activeTab === 'purchase' ? 'bg-white text-secondary shadow-sm' : 'text-gray-500'}`}
          >
            Choose Plan
          </button>
          <button 
            onClick={() => setActiveTab('history')}
            className={`flex-1 py-2 text-sm font-bold rounded-lg transition-all ${activeTab === 'history' ? 'bg-white text-secondary shadow-sm' : 'text-gray-500'}`}
          >
            History
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto w-full">
        <AnimatePresence mode="wait">
          {activeTab === 'purchase' ? (
            <motion.div 
              key="purchase"
              variants={containerVariants} initial="hidden" animate="visible" exit={{ opacity: 0 }}
              className="px-5 pt-6 space-y-8"
            >
              
              {/* TIER CARDS */}
              <div className="space-y-3">
                <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest flex items-center gap-2">
                  1. Select a Tier
                </h2>
                
                <div className="flex gap-4 overflow-x-auto pb-4 pt-2 scrollbar-hide snap-x">
                  {tiersData?.tiers?.map((tier) => {
                    const isSelected = selectedTierKey === tier.tier;
                    const isPopular = tier.tier === 'standard';
                    return (
                      <div 
                        key={tier.tier}
                        onClick={() => setSelectedTierKey(tier.tier)}
                        className={`snap-center shrink-0 w-[260px] p-5 rounded-3xl border-2 cursor-pointer transition-all relative ${
                          isSelected ? 'border-primary bg-orange-50/30 shadow-md shadow-orange-100' : 'border-gray-100 bg-white hover:border-gray-200'
                        }`}
                      >
                         {isPopular && (
                           <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-orange-500 to-amber-500 text-white text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider shadow-sm flex items-center gap-1"><Star size={10} fill="white"/> Most Popular</div>
                         )}
                         <div className="flex justify-between items-center mb-1">
                           <h3 className="text-lg font-extrabold text-secondary capitalize">{tier.tier}</h3>
                           {isSelected && <CheckCircle size={20} className="text-primary" />}
                         </div>
                         <p className="text-gray-500 text-xs font-medium mb-3 min-h-[32px]">{tier.tier_label}</p>
                         
                         <div className="mb-4">
                           <span className="text-3xl font-extrabold tracking-tight">₹{tier.final_weekly_premium}</span>
                           <span className="text-sm text-gray-400 font-medium">/wk</span>
                         </div>
                         
                         <div className="space-y-2 mt-4 pt-4 border-t border-gray-100">
                           <div className="flex items-start gap-2 text-sm text-gray-600">
                             <Check size={16} className="text-green-500 mt-0.5 shrink-0" strokeWidth={3}/>
                             <span>Up to <b>₹{tier.max_payout_per_event}</b> payout/event</span>
                           </div>
                           <div className="flex items-start gap-2 text-sm text-gray-600">
                             <Check size={16} className="text-green-500 mt-0.5 shrink-0" strokeWidth={3}/>
                             <span>Max <b>{tier.max_events_per_week} events</b> covered</span>
                           </div>
                         </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* PRICE BREAKDOWN */}
              {selectedTierData && (
                <motion.div variants={itemVariants} className="bg-white p-5 rounded-3xl border border-gray-100 shadow-sm relative overflow-hidden">
                   <div className="absolute top-0 right-0 p-4 opacity-10"><Info size={80} /></div>
                   <h2 className="text-sm font-bold text-gray-800 uppercase tracking-widest relative z-10 mb-4 flex items-center gap-2">
                     2. Price Breakdown
                   </h2>
                   <div className="space-y-3 relative z-10 text-sm">
                     <p className="text-xs text-gray-500 font-medium mb-1 bg-yellow-50 px-3 py-2 rounded-lg border border-yellow-100 text-yellow-800 flex items-start gap-2">
                       <Info size={14} className="mt-0.5 shrink-0"/> Transparency is KEY. This is the exact AI-calculated price just for you, {tiersData?.user_id}.
                     </p>
                     
                     {selectedTierData.factors_explanation.map((factor, idx) => {
                       const isPos = factor.includes('+');
                       const isNeg = factor.includes('-');
                       return (
                         <div key={idx} className="flex justify-between items-start border-b border-gray-50 pb-2 last:border-0 last:pb-0">
                           <span className="text-gray-600 font-medium pr-4">{factor.split(': ')[0] || factor}</span>
                           <span className={`font-mono font-bold shrink-0 ${isPos ? 'text-red-500' : (isNeg ? 'text-green-600' : 'text-gray-400')}`}>
                             {factor.split(': ')[1] || ''}
                           </span>
                         </div>
                       );
                     })}
                     
                     <div className="pt-3 mt-1 border-t-2 border-dashed border-gray-200 flex justify-between items-center">
                       <span className="font-extrabold text-secondary">Your weekly premium</span>
                       <span className="font-extrabold text-2xl tracking-tight text-primary">₹{selectedTierData.final_weekly_premium}</span>
                     </div>
                   </div>
                </motion.div>
              )}

            </motion.div>
          ) : (
            <motion.div 
              key="history"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="px-5 pt-6 space-y-6"
            >
               {/* HISTORY SUMMARY */}
               {historyData?.aggregate && (
                 <div className="bg-secondary text-white p-5 rounded-3xl shadow-lg relative overflow-hidden">
                   <div className="absolute -right-4 -bottom-4 w-32 h-32 bg-white/5 rounded-full blur-xl"></div>
                   <h3 className="text-white/60 text-xs font-bold uppercase tracking-widest mb-3">Lifetime Summary</h3>
                   <div className="grid grid-cols-2 gap-4">
                     <div>
                       <p className="text-white/60 text-xs font-medium">Total Invested</p>
                       <p className="text-xl font-bold font-mono mt-0.5">₹{historyData.aggregate.total_premiums_paid}</p>
                     </div>
                     <div>
                       <p className="text-white/60 text-xs font-medium">Total Received</p>
                       <p className="text-xl font-bold font-mono mt-0.5 text-green-400">₹{historyData.aggregate.total_payouts_received}</p>
                     </div>
                   </div>
                   <div className="mt-4 pt-3 border-t border-white/10 flex justify-between items-center">
                     <span className="text-sm font-bold text-white/80">Net Benefit</span>
                     <span className={`font-mono font-bold px-2.5 py-1 rounded text-sm ${historyData.aggregate.net_benefit >= 0 ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                       {historyData.aggregate.net_benefit >= 0 ? '+' : ''}₹{historyData.aggregate.net_benefit}
                     </span>
                   </div>
                   <p className="text-xs text-white/50 mt-3 flex items-center gap-1.5"><Info size={12}/> {historyData.aggregate.net_indicator}</p>
                 </div>
               )}

               {/* TIMELINE */}
               <div className="space-y-4 pb-8">
                 {historyData?.history?.map((pol, idx) => (
                   <div key={pol.policy_id} className="bg-white p-4 rounded-2xl border border-gray-100 shadow-sm flex flex-col relative">
                     <div className="flex justify-between items-start mb-3 border-b border-gray-50 pb-2">
                       <div>
                         <span className="text-[10px] font-bold uppercase tracking-widest bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{pol.tier}</span>
                         <p className="text-xs font-bold text-gray-800 mt-1.5">{pol.week}</p>
                       </div>
                       {pol.was_active && (
                         <span className="text-[10px] font-bold uppercase bg-green-50 text-green-600 px-2 py-0.5 rounded border border-green-100">Active</span>
                       )}
                     </div>
                     
                     <div className="grid grid-cols-3 gap-2 text-center text-sm">
                       <div>
                         <p className="text-gray-400 text-[10px] font-bold uppercase">Paid</p>
                         <p className="font-mono font-bold text-secondary">₹{pol.premium_paid}</p>
                       </div>
                       <div>
                         <p className="text-gray-400 text-[10px] font-bold uppercase">Claims</p>
                         <p className="font-mono font-bold text-secondary">{pol.claims_triggered}</p>
                       </div>
                       <div>
                         <p className="text-gray-400 text-[10px] font-bold uppercase">Net</p>
                         <p className={`font-mono font-bold ${pol.net_benefit >= 0 ? 'text-green-500' : 'text-red-400'}`}>
                           {pol.net_benefit >= 0 ? '+' : ''}₹{pol.net_benefit}
                         </p>
                       </div>
                     </div>
                   </div>
                 ))}
                 
                 {(!historyData?.history || historyData.history.length === 0) && (
                   <div className="text-center py-10 bg-white rounded-3xl border border-dashed border-gray-200">
                     <Clock size={32} className="mx-auto text-gray-300 mb-2"/>
                     <p className="text-gray-500 text-sm font-medium">No policy history yet.</p>
                   </div>
                 )}
               </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* FLOATING ACTION BOTTOM */}
      {activeTab === 'purchase' && selectedTierData && (
        <div className="fixed bottom-24 left-0 right-0 max-w-md mx-auto px-5 z-40">
           <button 
             onClick={handlePurchase}
             disabled={processing}
             className="w-full bg-primary text-white py-4 rounded-2xl font-extrabold shadow-[0_10px_25px_-5px_rgba(255,107,53,0.4)] flex justify-center items-center gap-2 active:scale-95 transition-all disabled:opacity-70"
           >
             {processing ? 'Processing...' : `Buy ${selectedTierData.tier.charAt(0).toUpperCase() + selectedTierData.tier.slice(1)} Cover • ₹${selectedTierData.final_weekly_premium}`}
             {!processing && <ChevronRight size={20} strokeWidth={3}/>}
           </button>
        </div>
      )}

      {/* BOTTOM NAVIGATION (Consistent w/ Dashboard) */}
      <div className="fixed bottom-0 left-0 right-0 w-full max-w-md mx-auto bg-white border-t border-gray-100 pb-safe pt-3 px-6 flex justify-between items-center z-50 pb-5">
        <Link to="/" className="flex flex-col items-center gap-1 cursor-pointer text-gray-400 hover:text-gray-600 transition-colors">
          <Home className="w-6 h-6" strokeWidth={2}/>
          <span className="text-[10px] font-semibold">Home</span>
        </Link>
        <Link to="/policy" className="flex flex-col items-center gap-1 cursor-pointer group">
          <div className="bg-primary/10 p-2 rounded-xl text-primary">
            <Shield className="w-6 h-6" strokeWidth={2.5}/>
          </div>
          <span className="text-[10px] font-bold text-primary">Policy</span>
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
