const defaultStaff = [
    { name: 'Michael Johnson', trade: 'Plumber', username: 'mjohnson', password: 'password123', showPassword: false },
    { name: 'Mark Davis', trade: 'Electrician', username: 'markd', password: 'password123', showPassword: false },
    { name: 'John Smith', trade: 'Carpenter', username: 'jsmith', password: 'password123', showPassword: false }
];

const storedStaff = JSON.parse(localStorage.getItem('smartSocietyStaff'));

const store = {
    staffList: storedStaff || defaultStaff,
    saveStaff: function() {
        localStorage.setItem('smartSocietyStaff', JSON.stringify(this.staffList));
    },
    notifications: [
        { id: 1, title: 'Urgent: Water Shutoff', text: 'Water will be shut off in Block B from 2 PM to 4 PM for emergency repairs.', time: '1h ago', read: false, type: 'alert', icon: 'fas fa-exclamation-triangle text-amber-500' },
        { id: 2, title: 'Pest Control Scheduled', text: 'Routine pest control for common areas this weekend.', time: '3h ago', read: true, type: 'info', icon: 'fas fa-bug text-indigo-500' }
    ],
    complaints: [
        { id: 'TKT-1001', category: 'Plumbing', subCategory: 'Leakage / Blockage', priority: 'High', status: 'In Progress', date: '01/07/2026 09:30 AM', resident: 'John Doe (B-101)', location: 'Master Bathroom', description: 'Continuous water leaking from the main tap.', assignedTo: 'Michael Johnson', history: [{date: '01/07/2026 09:30 AM', action: 'Request Logged'}, {date: '01/07/2026 10:15 AM', action: 'Assigned Task'}, {date: '01/07/2026 11:00 AM', action: 'Work Commenced'}], feedback: null },
        { id: 'TKT-1002', category: 'Electrical', subCategory: 'Appliance Malfunction', priority: 'High', status: 'Resolved', date: '28/06/2026 11:00 AM', resident: 'Jane Smith (A-204)', location: 'Tower A Lift 2', description: 'Lift is stuck on the 4th floor.', assignedTo: 'David Smith', history: [{date: '28/06/2026 11:00 AM', action: 'Request Logged'}, {date: '28/06/2026 02:00 PM', action: 'Work Completed'}], feedback: null },
        { id: 'TKT-1003', category: 'Electrical', subCategory: 'Power Outage', priority: 'Low', status: 'Closed', date: '10/05/2026 08:00 AM', resident: 'Alice Johnson (C-305)', location: 'Central Park Path', description: 'Street light flickering.', assignedTo: 'David Smith', history: [{date: '10/05/2026 08:00 AM', action: 'Request Logged'},{date: '11/05/2026 09:00 AM', action: 'Work Completed'}], feedback: {rating: '5', comment: 'Replaced quickly, thank you!'} },
        { id: 'TKT-1004', category: 'Plumbing', subCategory: 'Fixture Broken', priority: 'Medium', status: 'Open', date: '02/07/2026 14:00 PM', resident: 'John Doe (B-101)', location: 'Kitchen Sink', description: 'Tap handle is broken.', assignedTo: null, history: [{date: '02/07/2026 14:00 PM', action: 'Request Logged'}], feedback: null },
        { id: 'TKT-1005', category: 'Janitorial', subCategory: 'Cleaning Required', priority: 'Medium', status: 'Reopened', date: '01/07/2026 10:00 AM', resident: 'John Doe (B-101)', location: 'Lobby', description: 'Spill not cleaned properly.', assignedTo: null, history: [{date: '30/06/2026 10:00 AM', action: 'Request Logged'}, {date: '30/06/2026 15:00 PM', action: 'Work Completed'}, {date: '01/07/2026 10:00 AM', action: 'Resident Rejected Fix'}], feedback: null },
        
        // --- ADDED HISTORICAL DATA FOR MAINTENANCE FALLBACK ACCOUNT ---
        {
            id: 'TKT-1008',
            category: 'HVAC',
            subCategory: 'Appliance Malfunction',
            priority: 'High',
            status: 'In Progress',
            date: '08/07/2026 08:00 AM',
            resident: 'Sarah Connor (A-102)',
            location: 'Living Room',
            description: 'AC unit is blowing warm air.',
            assignedTo: 'Maintenance Team',
            history: [{date: '08/07/2026 08:00 AM', action: 'Assigned Task'}, {date: '08/07/2026 09:00 AM', action: 'Work Commenced'}],
            feedback: null
        },
        {
            id: 'TKT-1009',
            category: 'Plumbing',
            subCategory: 'Leakage / Blockage',
            priority: 'Medium',
            status: 'Resolved',
            date: '05/07/2026 09:00 AM',
            resident: 'John Doe (B-101)',
            location: 'Guest Bathroom',
            description: 'Leaking shower head fixed.',
            assignedTo: 'Maintenance Team',
            history: [{date: '05/07/2026 10:00 AM', action: 'Work Completed'}],
            feedback: {rating: '4', comment: 'Good job overall.'}
        },
        {
            id: 'TKT-1010',
            category: 'Electrical',
            subCategory: 'Power Outage',
            priority: 'Low',
            status: 'Closed',
            date: '01/07/2026 11:00 AM',
            resident: 'Alice Johnson (C-305)',
            location: 'Kitchen',
            description: 'Faulty switch replaced.',
            assignedTo: 'Maintenance Team',
            history: [{date: '01/07/2026 12:00 PM', action: 'Work Completed'}],
            feedback: {rating: '5', comment: 'Very professional, clean work!'}
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