const store = {
    staffList: [
        { name: 'Michael Johnson', trade: 'Plumber' },
        { name: 'David Smith', trade: 'Electrician' },
        { name: 'James Williams', trade: 'Carpenter' },
        { name: 'Robert Davis', trade: 'Janitorial' },
        { name: 'William Brown', trade: 'Security' }
    ],
    notifications: [
        { id: 1, title: 'System Maintenance', text: 'Platform offline Sunday 2 AM.', time: '2h ago', read: false, type: 'system', icon: 'fas fa-server' },
        { id: 2, title: 'Policy Update', text: 'New pool timings are in effect.', time: '1d ago', read: true, type: 'info', icon: 'fas fa-info-circle' }
    ],
    complaints: [
        { id: 'TKT-1001', category: 'Plumbing', subCategory: 'Leakage / Blockage', priority: 'High', status: 'In Progress', date: '01/07/2026 09:30 AM', resident: 'John Doe (B-101)', location: 'Master Bathroom', description: 'Continuous water leaking from the main tap.', assignedTo: 'Michael Johnson', history: [{date: '01/07/2026 09:30 AM', action: 'Request Logged'}, {date: '01/07/2026 10:15 AM', action: 'Assigned Task'}, {date: '01/07/2026 11:00 AM', action: 'Work Commenced'}], feedback: null },
        { id: 'TKT-1002', category: 'Electrical', subCategory: 'Appliance Malfunction', priority: 'High', status: 'Resolved', date: '28/06/2026 11:00 AM', resident: 'Jane Smith (A-204)', location: 'Tower A Lift 2', description: 'Lift is stuck on the 4th floor.', assignedTo: 'David Smith', history: [{date: '28/06/2026 11:00 AM', action: 'Request Logged'}, {date: '28/06/2026 02:00 PM', action: 'Work Completed'}], feedback: null },
        { id: 'TKT-1003', category: 'Electrical', subCategory: 'Power Outage', priority: 'Low', status: 'Closed', date: '10/05/2026 08:00 AM', resident: 'Alice Johnson (C-305)', location: 'Central Park Path', description: 'Street light flickering.', assignedTo: 'David Smith', history: [{date: '10/05/2026 08:00 AM', action: 'Request Logged'},{date: '11/05/2026 09:00 AM', action: 'Work Completed'}], feedback: {rating: '5', comment: 'Replaced quickly, thank you!'} },
        { id: 'TKT-1004', category: 'Plumbing', subCategory: 'Fixture Broken', priority: 'Medium', status: 'Open', date: '02/07/2026 14:00 PM', resident: 'John Doe (B-101)', location: 'Kitchen Sink', description: 'Tap handle is broken.', assignedTo: null, history: [{date: '02/07/2026 14:00 PM', action: 'Request Logged'}], feedback: null },
        { id: 'TKT-1005', category: 'Janitorial', subCategory: 'Cleaning Required', priority: 'Medium', status: 'Reopened', date: '01/07/2026 10:00 AM', resident: 'John Doe (B-101)', location: 'Lobby', description: 'Spill not cleaned properly.', assignedTo: null, history: [{date: '30/06/2026 10:00 AM', action: 'Request Logged'}, {date: '30/06/2026 15:00 PM', action: 'Work Completed'}, {date: '01/07/2026 10:00 AM', action: 'Resident Rejected Fix'}], feedback: null },
        
        // --- ADDED HISTORICAL DATA FOR STAFF ---
        { 
            id: 'TKT-1006', 
            category: 'Plumbing', 
            subCategory: 'Pipe Repair', 
            priority: 'High', 
            status: 'Resolved', 
            date: '29/06/2026 10:00 AM', 
            resident: 'John Doe (B-101)', 
            location: 'Kitchen Sink', 
            description: 'Fixed leaking pipe under sink.', 
            assignedTo: 'Michael Johnson', 
            history: [{date: '29/06/2026 10:00 AM', action: 'Work Completed'}], 
            feedback: {rating: '5', comment: 'Excellent work!'} 
        },
        { 
            id: 'TKT-1007', 
            category: 'Plumbing', 
            subCategory: 'Drainage', 
            priority: 'Medium', 
            status: 'Closed', 
            date: '25/06/2026 09:00 AM', 
            resident: 'Alice Johnson (C-305)', 
            location: 'Utility Room', 
            description: 'Unclogged floor drain.', 
            assignedTo: 'Michael Johnson', 
            history: [{date: '25/06/2026 09:00 AM', action: 'Work Completed'}], 
            feedback: {rating: '4', comment: 'Issue resolved.'} 
        }
    ],
    messages: [],
    getCaseMessages: function(caseId) {
        return this.messages.filter(m => m.caseId === caseId);
    },
    addCaseMessage: function(caseId, from, text, role) {
        this.messages.push({
            id: Date.now(),
            caseId: caseId,
            from: from,
            fromRole: role,
            text: text,
            timestamp: Date.now(),
            read: false
        });
    }
};