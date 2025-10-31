import React, { useState } from 'react';

export default function Settings() {
  const [host, setHost] = useState('127.0.0.1');
  const [port, setPort] = useState('9933');
  const [status, setStatus] = useState<string>('');
  const [loading, setLoading] = useState(false);

  async function onTest() {
    setLoading(true);
    setStatus('');
    try {
      const url = `http://127.0.0.1:8000/clo/health?host=${encodeURIComponent(host)}&port=${encodeURIComponent(port)}`;
      const res = await fetch(url);
      const j = await res.json();
      setStatus(j.ok ? `✅ ${j.advice || 'OK'}` : `❌ ${j.advice || 'Error'}`);
    } catch (e: any) {
      setStatus(`❌ ${e?.message || 'Request failed'}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 16 }}>
      <h2>Settings</h2>
      <div style={{ marginTop: 12 }}>
        <label>Host&nbsp;</label>
        <input value={host} onChange={(e) => setHost(e.target.value)} />
      </div>
      <div style={{ marginTop: 8 }}>
        <label>Port&nbsp;</label>
        <input value={port} onChange={(e) => setPort(e.target.value)} />
      </div>
      <div style={{ marginTop: 12 }}>
        <button onClick={onTest} disabled={loading}>
          {loading ? 'Testing…' : 'Test Port Now'}
        </button>
        <span style={{ marginLeft: 12 }}>{status}</span>
      </div>
    </div>
  );
}
