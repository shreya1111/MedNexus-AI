'use client';
import { useState, useRef, useEffect } from 'react';
import { Brain, Send, RefreshCw, User, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { aiApi } from '@/lib/api';
import { v4 as uuidv4 } from 'uuid';
import { useAuthStore } from '@/store/authStore';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const SUGGESTIONS = [
  'What are common symptoms of type 2 diabetes?',
  'Explain my last lab result values',
  'What lifestyle changes help with hypertension?',
  'When should I see a cardiologist?',
];

export default function AIAssistantPage() {
  const { user } = useAuthStore();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMsg: Message = { id: uuidv4(), role: 'user', content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const res = await aiApi.query(text, sessionId);
      const answer = res.data?.answer || res.data?.data?.answer || 'I could not find a relevant answer. Please consult a medical professional.';
      setMessages((prev) => [...prev, { id: uuidv4(), role: 'assistant', content: answer, timestamp: new Date() }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          role: 'assistant',
          content: '⚠️ The AI service is currently unavailable. Please ensure the RAG engine is running on port 8000.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-120px)] flex-col space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Medical Assistant</h1>
          <p className="text-gray-500 mt-1">Powered by LangChain RAG + Gemini AI</p>
        </div>
        <Button variant="outline" size="sm" onClick={() => setMessages([])}>
          <RefreshCw className="h-4 w-4" /> New chat
        </Button>
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <CardContent className="flex flex-1 flex-col p-0 overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-purple-50 mb-4">
                  <Brain className="h-8 w-8 text-purple-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Medical AI at your service</h3>
                <p className="text-gray-500 mb-6 max-w-md text-sm">
                  Ask medical questions, get summaries of your health records, understand lab values, or seek general health guidance.
                </p>
                <div className="grid gap-2 sm:grid-cols-2 max-w-lg">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      onClick={() => send(s)}
                      className="rounded-xl border border-gray-200 px-4 py-3 text-left text-sm text-gray-700 hover:border-purple-300 hover:bg-purple-50 transition-colors"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white text-sm font-semibold
                  ${msg.role === 'user' ? 'bg-blue-600' : 'bg-purple-600'}`}>
                  {msg.role === 'user' ? (user?.firstName?.[0] || <User className="h-4 w-4" />) : '🤖'}
                </div>
                <div className={`max-w-[75%] rounded-2xl px-4 py-3 text-sm
                  ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-sm' : 'bg-gray-100 text-gray-800 rounded-tl-sm'}`}>
                  <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  <p className={`mt-1 text-xs ${msg.role === 'user' ? 'text-blue-200' : 'text-gray-400'}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-600 text-white">🤖</div>
                <div className="rounded-2xl rounded-tl-sm bg-gray-100 px-4 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-gray-500" />
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="border-t border-gray-100 p-4">
            <div className="flex items-end gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input); } }}
                placeholder="Ask a medical question… (Enter to send, Shift+Enter for newline)"
                rows={2}
                className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:border-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/20"
              />
              <Button onClick={() => send(input)} disabled={!input.trim() || loading} className="bg-purple-600 hover:bg-purple-700 h-11 px-4">
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-2 text-xs text-gray-400 text-center">
              ⚕️ AI responses are for informational purposes only. Always consult a qualified physician.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
