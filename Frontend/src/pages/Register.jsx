import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Smartphone, User, MapPin, CheckCircle, ShieldCheck, ChevronRight, Loader2, IndianRupee } from 'lucide-react';
import api from '../api/client';

export default function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [formData, setFormData] = useState({
    phone: '',
    otp: '',
    name: '',
    platform: '',
    hours: '',
    city: '',
    zone: '',
    sub_zone: '',
    upi_id: '',
    aadhaar_last4: '',
    termsBase: false,
  });

  const [tempToken, setTempToken] = useState('');
  const [zonesData, setZonesData] = useState({});
  const [cities, setCities] = useState([]);

  useEffect(() => {
    async function fetchZones() {
      try {
        const res = await api.get('/v1/zones');
        setZonesData(res.data.zones);
        setCities(Object.keys(res.data.zones));
      } catch (err) {
        console.error("Failed to fetch zones");
      }
    }
    fetchZones();
  }, []);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCityChange = (e) => {
    const city = e.target.value;
    setFormData(prev => ({
      ...prev,
      city: city,
      zone: city, // City maps to zone intuitively in backend
      sub_zone: zonesData[city]?.[0] || ''
    }));
  };

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const formattedPhone = formData.phone.startsWith('+91') 
                           ? formData.phone 
                           : `+91${formData.phone}`;
      
      const res = await api.post('/auth/send-otp', { phone: formattedPhone });
      // The hint contains the OTP in DEV. We auto-fill it here to avoid popup blockers!
      const devOtp = (res.data.hint || '').replace('DEV OTP: ', '');
      setFormData(prev => ({ ...prev, phone: formattedPhone, otp: devOtp }));
      setStep(1.5); // OTP verification sub-step
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/verify-otp', {
        phone: formData.phone,
        otp: formData.otp
      });
      if (res.data.existing_user) {
        // Technically they should be logged in, redirect to dashboard
        localStorage.setItem('access_token', res.data.access_token);
        navigate('/');
      } else {
        setTempToken(res.data.temp_token);
        setStep(2);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const submitFinal = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.post('/auth/register', {
        temp_token: tempToken,
        name: formData.name,
        platform: formData.platform,
        city: formData.city,
        zone: formData.zone,
        sub_zone: formData.sub_zone,
        upi_id: formData.upi_id,
        aadhaar_last4: formData.aadhaar_last4
      });
      localStorage.setItem('access_token', res.data.access_token);
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to register');
    } finally {
      setLoading(false);
    }
  };

  const renderProgressBar = () => {
    const steps = [
      { id: 1, name: 'Phone', icon: Smartphone, act: step >= 1 },
      { id: 2, name: 'About You', icon: User, act: step >= 2 },
      { id: 3, name: 'Zone', icon: MapPin, act: step >= 3 },
      { id: 4, name: 'Done', icon: CheckCircle, act: step >= 4 }
    ];
    
    return (
      <div className="flex items-center justify-between mb-8 relative">
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 -z-10 rounded"></div>
        <div 
          className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-primary -z-10 rounded transition-all duration-300"
          style={{ width: `${((Math.floor(step) - 1) / 3) * 100}%` }}
        ></div>
        
        {steps.map((s) => (
          <div key={s.id} className="flex flex-col items-center">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center border-4 ${s.act ? 'bg-primary border-orange-200 text-white' : 'bg-white border-gray-200 text-gray-400'} transition-colors duration-300`}>
              <s.icon size={18} />
            </div>
            <span className={`text-xs mt-2 font-medium ${s.act ? 'text-secondary' : 'text-gray-400'}`}>{s.name}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pt-6 pb-12 px-4 sm:px-6">
      
      {/* Header */}
      <div className="flex flex-col items-center justify-center mb-8">
        <div className="flex items-center gap-2 mb-2">
          <ShieldCheck className="text-primary" size={36} strokeWidth={2.5}/>
          <h1 className="text-3xl font-extrabold text-secondary tracking-tight">ShiftShield</h1>
        </div>
        <p className="text-sm text-gray-500 font-medium">Income protection that works as hard as you do</p>
      </div>

      <div className="max-w-md w-full mx-auto">
        {renderProgressBar()}

        <form className="bg-white rounded-2xl shadow-xl overflow-hidden p-6 sm:p-8 border border-gray-100">
          
          {error && (
            <div className="mb-6 bg-red-50 text-red-600 p-3 rounded-lg text-sm font-medium border border-red-100 flex items-center gap-2">
              <span className="block w-2 h-2 bg-red-500 rounded-full"></span>
              {error}
            </div>
          )}

          {/* STEP 1: Phone & OTP */}
          {Math.floor(step) === 1 && (
            <div className="space-y-6 animate-in slide-in-from-right fade-in duration-300">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-secondary">Let's get started</h2>
                <p className="text-gray-500 mt-1">Enter your mobile number</p>
              </div>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Phone Number</label>
                  <div className="relative flex items-center">
                    <span className="absolute left-4 text-gray-500 font-medium">+91</span>
                    <input 
                      type="tel" 
                      name="phone"
                      value={formData.phone.replace('+91', '')}
                      onChange={handleChange}
                      disabled={step === 1.5}
                      className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition disabled:bg-gray-50 disabled:text-gray-500 font-medium text-lg"
                      placeholder="98765 43210"
                      maxLength={10}
                    />
                  </div>
                </div>

                {step === 1 && (
                  <button onClick={handleSendOTP} disabled={loading || formData.phone.length < 10} className="w-full bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-orange-600 active:scale-[0.98] transition-all flex items-center justify-center disabled:opacity-70">
                    {loading ? <Loader2 className="animate-spin" /> : 'Send OTP'}
                  </button>
                )}

                {step === 1.5 && (
                  <div className="animate-in fade-in slide-in-from-top-4 duration-300 pt-4 border-t border-gray-100 mt-6">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Enter 6-digit OTP</label>
                    <input 
                      type="text" 
                      name="otp"
                      value={formData.otp}
                      onChange={handleChange}
                      className="w-full text-center tracking-[0.5em] text-2xl py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition"
                      placeholder="••••••"
                      maxLength={6}
                      autoFocus
                    />
                    <button onClick={handleVerifyOTP} disabled={loading || formData.otp.length < 6} className="w-full mt-4 bg-secondary text-white font-bold py-3.5 rounded-xl hover:bg-slate-800 active:scale-[0.98] transition-all flex items-center justify-center shadow-md disabled:opacity-70">
                      {loading ? <Loader2 className="animate-spin" /> : 'Verify & Continue'}
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* STEP 2: About You */}
          {step === 2 && (
            <div className="space-y-6 animate-in slide-in-from-right fade-in duration-300">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-secondary">About You</h2>
                <p className="text-gray-500 mt-1">Help us personalize your policy</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Full Name</label>
                <input 
                  type="text" 
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition"
                  placeholder="e.g. Rahul Sharma"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-3">Primary Platform</label>
                <div className="grid grid-cols-3 gap-3">
                  <div 
                    onClick={() => setFormData({...formData, platform: 'swiggy'})}
                    className={`cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center justify-center transition-all ${formData.platform === 'swiggy' ? 'border-orange-500 bg-orange-50 shadow-sm' : 'border-gray-200 hover:border-orange-200'}`}
                  >
                    <div className="w-8 h-8 rounded-full bg-[#FC8019] mb-2 shadow-sm"></div>
                    <span className="text-xs font-bold text-gray-700">Swiggy</span>
                  </div>
                  
                  <div 
                    onClick={() => setFormData({...formData, platform: 'zomato'})}
                    className={`cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center justify-center transition-all ${formData.platform === 'zomato' ? 'border-red-500 bg-red-50 shadow-sm' : 'border-gray-200 hover:border-red-200'}`}
                  >
                    <div className="w-8 h-8 rounded-full bg-[#E23744] mb-2 shadow-sm"></div>
                    <span className="text-xs font-bold text-gray-700">Zomato</span>
                  </div>

                  <div 
                    onClick={() => setFormData({...formData, platform: 'both'})}
                    className={`cursor-pointer border-2 rounded-xl p-3 flex flex-col items-center justify-center transition-all ${formData.platform === 'both' ? 'border-indigo-500 bg-indigo-50 shadow-sm' : 'border-gray-200 hover:border-indigo-200'}`}
                  >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#FC8019] to-[#E23744] mb-2 shadow-sm"></div>
                    <span className="text-xs font-bold text-gray-700">Both</span>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Working Hours</label>
                <select 
                  name="hours"
                  value={formData.hours}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition bg-white"
                >
                  <option value="">Select your typical shift</option>
                  <option value="morning">Morning (6 AM - 2 PM)</option>
                  <option value="afternoon">Afternoon (2 PM - 10 PM)</option>
                  <option value="night">Night Delivery (10 PM Onwards)</option>
                  <option value="full">Full Day (Flexible)</option>
                </select>
              </div>

              <button 
                onClick={(e) => { e.preventDefault(); setStep(3); }}
                disabled={!formData.name || !formData.platform || !formData.hours}
                className="w-full bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-orange-600 active:scale-[0.98] transition-all flex items-center justify-center shadow-md disabled:opacity-50 mt-8"
              >
                Next Step <ChevronRight size={20} className="ml-1" />
              </button>
            </div>
          )}

          {/* STEP 3: Your Zone */}
          {step === 3 && (
            <div className="space-y-6 animate-in slide-in-from-right fade-in duration-300">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-secondary">Your Work Zone</h2>
                <p className="text-gray-500 mt-1">Risk and premium are calculated based on your city</p>
              </div>

              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">City</label>
                  <select 
                    name="city"
                    value={formData.city}
                    onChange={handleCityChange}
                    className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition bg-white font-medium text-gray-800"
                  >
                    <option value="" disabled>Select City</option>
                    {cities.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>

                {formData.city && zonesData[formData.city] && (
                  <div className="animate-in fade-in duration-300">
                    <label className="block text-sm font-semibold text-gray-700 mb-2">Specific Routing Sub-zone</label>
                    <select 
                      name="sub_zone"
                      value={formData.sub_zone}
                      onChange={handleChange}
                      className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition bg-white"
                    >
                      {zonesData[formData.city].map(z => <option key={z} value={z}>{z}</option>)}
                    </select>
                  </div>
                )}
              </div>

              {formData.city && formData.sub_zone && (
                <div className="mt-6 bg-slate-50 border border-slate-200 rounded-xl p-4 animate-in fade-in slide-in-from-bottom-2">
                  <div className="flex items-start gap-3">
                    <div className="bg-orange-100 p-2 rounded-lg text-primary">
                      <MapPin size={20} />
                    </div>
                    <div>
                      <h4 className="font-bold text-gray-800 text-sm">Zone Insights: {formData.sub_zone}</h4>
                      <p className="text-xs text-gray-500 mt-1 mb-3 leading-relaxed">
                        Risk multipliers applied based on historical weather events and local topography. High risk detected for intense rainfall and waterlogging.
                      </p>
                      <div className="flex items-center gap-1.5 py-1 px-3 bg-green-50 text-green-700 text-xs font-bold rounded-md w-fit border border-green-100">
                        <IndianRupee size={12} />
                        Estimated Premium: ₹79 - ₹180 / week
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <button 
                onClick={(e) => { e.preventDefault(); setStep(4); }}
                disabled={!formData.city || !formData.sub_zone}
                className="w-full mt-8 bg-primary text-white font-bold py-3.5 rounded-xl hover:bg-orange-600 active:scale-[0.98] transition-all flex items-center justify-center shadow-md disabled:opacity-50"
              >
                Almost Done <ChevronRight size={20} className="ml-1" />
              </button>
            </div>
          )}

          {/* STEP 4: Almost Done */}
          {step === 4 && (
            <div className="space-y-6 animate-in slide-in-from-right fade-in duration-300">
               <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-secondary">Final Setup</h2>
                <p className="text-gray-500 mt-1">Where should we send your payouts?</p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">UPI ID (For Payouts)</label>
                <input 
                  type="text" 
                  name="upi_id"
                  value={formData.upi_id}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition"
                  placeholder="e.g. rahul@paytm or 9876543210@ybl"
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Aadhaar Last 4 Digits<span className="text-xs text-gray-400 font-normal ml-2">(KYC)</span></label>
                <input 
                  type="text" 
                  name="aadhaar_last4"
                  value={formData.aadhaar_last4}
                  onChange={handleChange}
                  maxLength={4}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-primary transition tracking-[0.2em] font-medium"
                  placeholder="XXXX"
                />
              </div>

              <div className="bg-orange-50/50 p-4 rounded-xl border border-orange-100 mt-6">
                <label className="flex items-start gap-3 cursor-pointer">
                  <div className="relative flex items-center pt-1">
                    <input 
                      type="checkbox"
                      name="termsBase"
                      checked={formData.termsBase}
                      onChange={handleChange}
                      className="w-5 h-5 border-2 border-primary rounded text-primary focus:ring-primary"
                    />
                  </div>
                  <span className="text-xs text-gray-600 leading-relaxed font-medium">
                    I understand this policy ONLY triggers for defined extreme weather events or disruptions (rainfall, AQI, heat, curfews) that result in income loss. <span className="text-primary font-semibold hover:underline cursor-pointer">Read Policy Terms</span>.
                  </span>
                </label>
              </div>

              <button 
                onClick={submitFinal}
                disabled={loading || !formData.upi_id || formData.aadhaar_last4.length < 4 || !formData.termsBase}
                className="w-full mt-4 bg-secondary text-white font-bold py-3.5 rounded-xl hover:bg-slate-800 active:scale-[0.98] transition-all flex items-center justify-center shadow-lg disabled:opacity-50"
              >
                {loading ? <Loader2 className="animate-spin" /> : (
                  <>Start Protection <ShieldCheck size={20} className="ml-2" strokeWidth={2.5}/></>
                )}
              </button>
            </div>
          )}
        </form>

        <p className="text-center text-xs text-gray-400 font-medium mt-8">
          Secured by ShiftShield Trust Environment 🔒
        </p>
      </div>
    </div>
  );
}
