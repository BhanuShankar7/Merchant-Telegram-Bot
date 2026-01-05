import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = "http://localhost:8000";

function App() {
  const [orders, setOrders] = useState([]);
  const [filter, setFilter] = useState('ALL'); // ALL, MEMBER, NON-MEMBER
  const [showOrderModal, setShowOrderModal] = useState(false);
  const [loading, setLoading] = useState(true);

  // Poll for updates
  useEffect(() => {
    fetchOrders();
    const interval = setInterval(fetchOrders, 3000); // 3s polling
    return () => clearInterval(interval);
  }, []);

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API_URL}/orders`);
      setOrders(res.data);
      setLoading(false);
    } catch (err) {
      console.error("Error fetching orders:", err);
    }
  };

  const getFilteredOrders = () => {
    // Exclude Completed orders from the visible list
    const visibleOrders = orders.filter(o => o.status !== 'Completed');

    if (filter === 'ALL') return visibleOrders;
    if (filter === 'MEMBER') return visibleOrders.filter(o => o.member_id && !o.member_id.toString().startsWith('Guest-') && o.member_id !== 'NON-MEMBER');
    if (filter === 'NON-MEMBER') return visibleOrders.filter(o => o.member_id === 'NON-MEMBER' || (o.member_id && o.member_id.toString().startsWith('Guest-')));
    return visibleOrders;
  };

  const stats = {
    total: orders.length,
    active: orders.filter(o => o.status === 'Active').length,
    revenue: orders.reduce((acc, curr) => {
      // Only count valid orders (Active or Completed)
      if (curr.status !== 'Cancelled') {
        return acc + (curr.amount || 0);
      }
      return acc;
    }, 0)
  };

  const handleComplete = async (orderId) => {
    try {
      await axios.post(`${API_URL}/complete-order/${orderId}`);
      fetchOrders(); // Refresh to make it disappear
    } catch (err) {
      console.error("Error completing order", err);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="logo">
          <h1>⚡ Neutrious Dashboard</h1>
          <span className="live-status">● Live</span>
        </div>
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-label">Total Orders</span>
            <span className="stat-value">{stats.total}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Active</span>
            <span className="stat-value active-text">{stats.active}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Revenue</span>
            <span className="stat-value">₹{stats.revenue}</span>
          </div>
        </div>
        <button className="primary-btn" onClick={() => setShowOrderModal(true)}>
          + New Order
        </button>
      </header>

      <main className="main-content">
        <div className="tabs">
          {['ALL', 'MEMBER', 'NON-MEMBER'].map(f => (
            <button
              key={f}
              className={`tab-btn ${filter === f ? 'active' : ''}`}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>

        <div className="orders-grid">
          {loading ? (
            <p>Loading orders...</p>
          ) : getFilteredOrders().length === 0 ? (
            <div className="empty-state">No orders found in this category.</div>
          ) : (
            getFilteredOrders().map(order => (
              <OrderCard key={order.id} order={order} onComplete={handleComplete} />
            ))
          )}
        </div>
      </main>

      {showOrderModal && (
        <PlaceOrderModal onClose={() => setShowOrderModal(false)} refresh={fetchOrders} />
      )}
    </div>
  );
}

function OrderCard({ order, onComplete }) {
  const isGuest = order.member_id === 'NON-MEMBER' || (order.member_id && order.member_id.toString().startsWith('Guest-'));
  const isMember = !isGuest;

  // Format ID for display
  let displayId = order.member_id;
  if (displayId && displayId.toString().startsWith("Guest-")) {
    displayId = displayId.split("-")[1]; // Show just 1234
  }

  return (
    <div className={`order-card ${order.status === 'Cancelled' ? 'cancelled' : ''}`}>
      <div className="card-header">
        <span className={`badge ${isMember ? 'badge-member' : 'badge-guest'}`}>
          {isMember ? 'MEMBER' : 'GUEST'}
        </span>
        <span className="order-time">
          {new Date(order.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      <div className="card-body">
        <h3>{isMember ? `ID: ${order.member_id}` : `ID: ${displayId}`}</h3>
        <div className="order-details">
          {order.items && (
            <div className="detail-row items-row">
              <span className="items-text">{order.items}</span>
            </div>
          )}
          <div className="detail-row">
            <span>Amount:</span>
            <strong>₹{order.amount}</strong>
          </div>
          <div className="detail-row">
            <span>Type:</span>
            <span>{order.type}</span>
          </div>
          {order.delivery_date && (
            <div className="detail-row">
              <span>Date:</span>
              <span>{order.delivery_date}</span>
            </div>
          )}
          <div className="detail-row">
            <span>Status:</span>
            <span className={`status-text ${order.status.toLowerCase()}`}>{order.status}</span>
          </div>
        </div>

        {order.status === 'Active' && (
          <button className="done-btn" onClick={() => onComplete(order.id)}>
            ✅ Done
          </button>
        )}
      </div>
    </div>
  );
}

function PlaceOrderModal({ onClose, refresh }) {
  const [formData, setFormData] = useState({
    member_id: '',
    amount: '',
    items: '',
    type: 'Immediate',
    isMember: false
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);

    const payload = {
      member_id: formData.isMember ? formData.member_id : "NON-MEMBER",
      amount: parseInt(formData.amount),
      items: formData.items,
      type: formData.type
    };

    try {
      await axios.post(`${API_URL}/place-order`, payload);
      refresh();
      onClose();
    } catch (err) {
      alert("Failed to place order. Check ID or Balance.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal">
        <div className="modal-header">
          <h2>New Order (Staff)</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={formData.isMember}
                onChange={e => setFormData({ ...formData, isMember: e.target.checked })}
              />
              Is Member?
            </label>
          </div>

          {formData.isMember && (
            <div className="form-group">
              <label>Member ID</label>
              <input
                type="text"
                required
                value={formData.member_id}
                onChange={e => setFormData({ ...formData, member_id: e.target.value })}
                placeholder="e.g. 97011"
              />
            </div>
          )}

          <div className="form-group">
            <label>Items (Description)</label>
            <input
              type="text"
              required
              value={formData.items}
              onChange={e => setFormData({ ...formData, items: e.target.value })}
              placeholder="e.g. 2x Salad"
            />
          </div>

          <div className="form-group">
            <label>Amount (₹)</label>
            <input
              type="number"
              required
              value={formData.amount}
              onChange={e => setFormData({ ...formData, amount: e.target.value })}
              placeholder="0"
            />
          </div>

          <div className="form-group">
            <label>Type</label>
            <select
              value={formData.type}
              onChange={e => setFormData({ ...formData, type: e.target.value })}
            >
              <option value="Immediate">Immediate / Dine-in</option>
              <option value="Takeaway">Takeaway</option>
              <option value="Pre-order">Pre-order</option>
            </select>
          </div>

          <button type="submit" className="submit-btn" disabled={submitting}>
            {submitting ? 'Placing...' : 'Confirm Order'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;
