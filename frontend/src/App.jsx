import React, { useState, useEffect } from 'react';
import { MessageSquare, Brain, Zap, Shield, Activity, Send, Loader2 } from 'lucide-react';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

function App() {
  const [mode, setMode] = useState('passive');
  const [challenge, setChallenge] = useState('monitor');
  const [message, setMessage] = useState('');
  const [objectives, setObjectives] = useState(['gather_intelligence', 'build_reputation']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [modes, setModes] = useState([]);
  const [challenges, setChallenges] = useState([]);

  useEffect(() => {
    // 获取可用的模式和挑战
    fetchModesAndChallenges();
  }, []);

  const fetchModesAndChallenges = async () => {
    try {
      const [modesRes, challengesRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/modes`),
        axios.get(`${API_BASE_URL}/challenges`)
      ]);
      setModes(modesRes.data.modes);
      setChallenges(challengesRes.data.challenges);
    } catch (err) {
      console.error('Failed to fetch modes and challenges:', err);
    }
  };

  const handleRunAgent = async () => {
    if (!message.trim()) {
      setError('请输入您的需求或消息');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/run`, {
        mode,
        challenge,
        message,
        objectives
      });

      if (response.data.success) {
        setResult(response.data);
      } else {
        setError(response.data.error || '运行失败');
      }
    } catch (err) {
      setError(err.response?.data?.error || err.message || '网络错误');
    } finally {
      setLoading(false);
    }
  };

  const getModeIcon = (modeValue) => {
    switch (modeValue) {
      case 'passive': return <Shield className="w-5 h-5" />;
      case 'active': return <Zap className="w-5 h-5" />;
      case 'competitive': return <Brain className="w-5 h-5" />;
      case 'defensive': return <Activity className="w-5 h-5" />;
      default: return <Brain className="w-5 h-5" />;
    }
  };

  return (
    <div className="min-h-screen text-white p-8">
      {/* Header */}
      <div className="max-w-6xl mx-auto mb-8">
        <div className="text-center animate-float">
          <h1 className="text-5xl font-bold mb-4 gradient-text">
            Zero Realm Social Agent
          </h1>
          <p className="text-xl text-white/70">
            高性能社交策略智能体 - 清晰识别您的需求
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Panel - Input */}
        <div className="space-y-6">
          {/* Mode Selection */}
          <div className="glass-card p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Brain className="w-6 h-6 text-cyan-400" />
              选择运行模式
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {modes.map((m) => (
                <button
                  key={m.value}
                  onClick={() => setMode(m.value)}
                  className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                    mode === m.value
                      ? 'border-cyan-400 bg-cyan-400/20 text-cyan-300'
                      : 'border-white/10 bg-white/5 text-white/70 hover:border-white/30'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    {getModeIcon(m.value)}
                    <span className="font-medium capitalize">{m.value}</span>
                  </div>
                  <p className="text-sm text-white/60">{m.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Challenge Selection */}
          <div className="glass-card p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <Zap className="w-6 h-6 text-cyan-400" />
              选择挑战类型
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {challenges.map((c) => (
                <button
                  key={c.value}
                  onClick={() => setChallenge(c.value)}
                  className={`p-4 rounded-xl border-2 transition-all duration-300 ${
                    challenge === c.value
                      ? 'border-cyan-400 bg-cyan-400/20 text-cyan-300'
                      : 'border-white/10 bg-white/5 text-white/70 hover:border-white/30'
                  }`}
                >
                  <span className="font-medium capitalize">{c.value}</span>
                  <p className="text-sm text-white/60 mt-1">{c.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Message Input */}
          <div className="glass-card p-6">
            <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
              <MessageSquare className="w-6 h-6 text-cyan-400" />
              您的需求
            </h2>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="请详细描述您的需求，Agent 将会认真理解并执行..."
              className="input-field h-32 resize-none"
            />
            <p className="text-sm text-white/50 mt-2">
              * Agent 会仔细分析您的需求，不会忽略任何重要信息
            </p>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunAgent}
            disabled={loading}
            className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                处理中...
              </>
            ) : (
              <>
                <Send className="w-5 h-5" />
                运行 Agent
              </>
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="glass-card p-4 border-red-500/50 bg-red-500/10">
              <p className="text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Right Panel - Results */}
        <div className="space-y-6">
          {result ? (
            <div className="glass-card p-6">
              <h2 className="text-2xl font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-6 h-6 text-cyan-400" />
                运行结果
              </h2>
              
              <div className="space-y-4">
                {/* Session Info */}
                <div className="bg-white/5 rounded-xl p-4">
                  <h3 className="font-medium text-cyan-300 mb-2">会话信息</h3>
                  <div className="space-y-1 text-sm">
                    <p><span className="text-white/60">会话 ID:</span> {result.session_id}</p>
                    <p><span className="text-white/60">Agent ID:</span> {result.agent_id}</p>
                    <p><span className="text-white/60">模式:</span> {result.current_mode}</p>
                    <p><span className="text-white/60">挑战:</span> {result.active_challenge}</p>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="bg-white/5 rounded-xl p-4">
                  <h3 className="font-medium text-cyan-300 mb-2">性能指标</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(result.performance_metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-white/60">{key}:</span>
                        <span className="text-white">{value.toFixed(3)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Messages */}
                <div className="bg-white/5 rounded-xl p-4">
                  <h3 className="font-medium text-cyan-300 mb-2">消息记录</h3>
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {result.messages.map((msg, index) => (
                      <div key={index} className="bg-white/5 rounded-lg p-3">
                        <p className="text-xs text-white/50 mb-1">{msg.timestamp}</p>
                        <p className="text-sm text-white/70">{msg.type}: {msg.content}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="glass-card p-12 text-center">
              <Brain className="w-16 h-16 text-cyan-400 mx-auto mb-4 animate-pulse-slow" />
              <p className="text-xl text-white/70">
                等待运行 Agent...
              </p>
              <p className="text-sm text-white/50 mt-2">
                在左侧配置参数并输入您的需求
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="max-w-6xl mx-auto mt-12 text-center text-white/40 text-sm">
        <p>Zero Realm Social Agent - 专为社交策略设计的高性能智能体</p>
        <p className="mt-1">确保每个用户需求都被认真理解和执行</p>
      </div>
    </div>
  );
}

export default App;
