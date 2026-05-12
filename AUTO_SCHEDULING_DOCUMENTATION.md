# TAZARA AI Train Scheduling System - Simple Guide

## Table of Contents
1. [How It Works](#how-it-works)
2. [Frontend Scheduling](#frontend-scheduling)
3. [Backend AI](#backend-ai)
4. [Priority System](#priority-system)
5. [Math Calculations](#math-calculations)
6. [AI Parts](#ai-parts)
7. [How Data Flows](#how-data-flows)
8. [Making It Fast](#making-it-fast)
9. [Settings and Numbers](#settings-and-numbers)

---

## How It Works

The TAZARA AI Train Scheduling System helps plan train routes automatically using smart computer programs:

1. **Rule-Based Planning** - Follows set rules for loading trains
2. **Learning AI** - Computer learns from experience to make better choices
3. **Priority System** - Handles important customer orders first
4. **Multi-Route Planning** - Plans trains across many different routes

The system can manage 1-12 trains on 6 main TAZARA railway routes, making smart decisions in real-time to save money and time.

---

## Frontend Scheduling

### 1. Regular Scheduling (`createSchedule()`)

**Where to find it**: `multi_route.html` lines 1084-1279

#### How It Works:
1. **Read customer orders** from what you select on screen
2. **Check and fix** cargo needs for each railway route
3. **Assign trains** using smart loading rules
4. **Calculate costs** for fuel and drivers
5. **Create daily plans** for each train
6. **Send plans** to the computer brain for processing

#### Main Functions:

**Getting Cargo Needs (`getCargoRequirementsFromOrders`)**
- Takes customer orders you selected
- Tells how much cargo goes on each route
- Example: Dar-Kapiri route needs 500 tons, Dar-Mbeya needs 300 tons

**Checking Orders:**
- Fixes wrong route names (uses Dar-Kapiri if unsure)
- Makes sure cargo amounts are positive numbers
- Removes bad orders

**Assigning Trains (`allocateTrainsSequentially`)**
- **Step 1**: Sort routes by most cargo first
- **Step 2**: Sort trains by biggest capacity first
- **Step 3**: For each route:
  - Give biggest trains to busiest routes
  - Calculate how much each train should carry
  - Assign drivers and calculate fuel costs

**Train Sizes:**
- Train 1: Heavy - carries 1000 tons
- Train 2: Medium - carries 800 tons  
- Train 3: Medium - carries 800 tons
- Train 4: Light - carries 600 tons
- Train 5: Light - carries 600 tons
- Train 6: Super Heavy - carries 1000 tons

**Fuel Costs:**
- Heavy trains: 60 ZMW per ton of cargo (more efficient at larger scale)
- Medium trains: 65 ZMW per ton
- Light trains: 70 ZMW per ton
- Super Heavy: 55 ZMW per ton (most efficient)

### 2. Priority Scheduling (`createAutoSchedule()`)

**Where to find it**: `multi_route.html` lines 2867-2943

#### How It Works:
1. **Get settings** - how many trains, how many days
2. **Ask AI brain** to make automatic schedule
3. **Process the plan** the AI created
4. **Show results** with priority breakdown

**What It Asks the AI:**
```
Please make schedule with:
- 5 trains
- 7 days maximum
- Include all waiting orders
- No order limit
```

---

## Backend AI

### 1. Learning AI for Multiple Routes

**Where to find it**: `api/routes/multi_route.py`

#### How the AI Brain Works:
The AI uses a special environment to learn how to schedule trains:
- **Environment**: Like a video game where AI practices scheduling
- **Agent**: The AI brain that makes decisions
- **Learning**: AI gets better by trying many times

#### AI Training Steps:
1. **Setup the game world** with trains, routes, and cargo
2. **Load the smart brain** that knows how to play
3. **Practice scheduling** day by day:
   - AI chooses what each train should do
   - For first 3 days, we make AI work (no lazy trains!)
   - AI tries its choices and sees what happens
   - AI remembers what worked well

#### Keeping Trains Busy:
The AI sometimes wants to let trains rest, but we make it work for the first 3 days:
- Find routes that need cargo moved
- Divide trains among busy routes
- This prevents lazy AI behavior early on

### 2. Priority Order System

**Where to find it**: `api/routes/priority_auto_scheduler.py`

#### How Priority Scoring Works:
Each customer order gets points based on importance:

**Base Priority Points:**
- Emergency (Level 1): +40 points
- Urgent (Level 2): +30 points  
- Priority (Level 3): +20 points
- Normal (Level 4): +10 points
- Low (Level 5): +5 points

**Extra Points for Urgency:**
- Due in 1 day: +30 points
- Due in 3 days: +20 points
- Due in 7 days: +10 points

**Bonus Points:**
- Big cargo (over 1000 tons): +10 points
- Medium cargo (over 500 tons): +5 points
- Emergency cargo (medical, etc.): +15 points
- Long routes (full TAZARA): +10 points
- Government customers: +5 points

**Maximum score: 100 points**

#### How Urgent is Departure?
- Leave today or tomorrow: +20 urgency points
- Leave within 3 days: +15 urgency points  
- Leave within 1 week: +10 urgency points
- Leave later: +0 urgency points

---

## Math Calculations

### 1. How Well Are We Doing? (Efficiency)
**Industry Goal**: 100 tons per train per day

**How we calculate it:**
- How much cargo each train actually carries per day
- Compare to the goal of 100 tons
- Show as a percentage (max 100%)

**Example**: If trains carry 80 tons per day each, efficiency = 80%

### 2. How Much Did We Deliver? (Delivery Rate)
**How we calculate it:**
- Add up all cargo customers wanted
- See how much we actually delivered
- Show as a percentage

**Example**: If customers wanted 1000 tons and we delivered 800 tons = 80%

### 3. Money Math (Cost Breakdown)
**Fixed Costs (same every day):**
- Crew pay: 1500 ZMW per train per day
- Maintenance: 800 ZMW per train per day

**Variable Costs (changes with cargo):**
- Fuel: Depends on how much cargo and which routes

**Money In:**
- Revenue: 120 ZMW per ton of cargo (average)

**Profit Calculation:**
```
Profit = Revenue - (Fuel Cost + Crew Cost + Maintenance Cost)
```

**Example**: 
- 1000 tons cargo = 120,000 ZMW revenue
- 5 trains for 3 days = 22,500 ZMW crew + 12,000 ZMW maintenance
- Fuel = 40,000 ZMW
- Profit = 120,000 - (40,000 + 22,500 + 12,000) = 45,500 ZMW

---

## AI Parts

### 1. Smart Learning Brain (DQN)
The AI brain works like this:
- **Brain Structure**: Many layers that learn from experience
- **What It Knows**: Where trains are, what cargo needs moving, what day it is
- **What It Can Do**: Send trains to routes or let them rest
- **How It Learns**: Gets points for good choices (moving cargo, saving money)

### 2. One-Size-Fits-All Brain
The same AI brain can handle any number of trains (1-12):
- **Brain File**: `multi_route_agent_tazara_network_fixed.pkl`
- **How It Works**: 
  - Counts how many routes exist
  - Adds 1 for "rest" option
  - Creates brain that can handle that many choices

### 3. Route Choices
The AI knows these 6 main routes:
- **DAR_KAPIRI**: Dar es Salaam to Kapiri Mposhi (longest route)
- **DAR_MBEYA**: Dar es Salaam to Mbeya
- **MBEYA_KASAMA**: Mbeya to Kasama
- **KAPIRI_NDOLA**: Kapiri Mposhi to Ndola
- **DAR_KIDATU**: Dar es Salaam to Kidatu
- **KIDATU_TRANS_SHIPMENT**: Kidatu Transshipment

Each route has different distances and takes different amounts of time.

---

## How Data Flows

### 1. From Screen to Computer Brain
```
You Click → JavaScript Thinks → Calls AI → AI Works → Saves to Database → Shows Results
```

### 2. How AI Makes Decisions
```
Customer Orders → Score Priorities → Pick Routes → Assign Trains → Calculate Costs → Make Schedule
```

### 3. Database Storage
The system uses a PostgreSQL database to store everything:
- **Customer Orders**: All the orders customers place
- **Schedules**: The train plans the AI creates
- **Daily Assignments**: What each train does each day
- **Cost Information**: Money calculations for each schedule

**Database Login Info:**
- Computer: localhost
- Database name: tazara_multi_route
- User: tazara
- Password: tazara123

---

## Making It Fast

### 1. Screen (Frontend) Speed Tricks
- **Load When Needed**: Only get schedule data when you ask for it
- **Remember Stuff**: Keep commonly used data in your browser
- **Don't Over-Call**: Wait a bit before making too many requests
- **Works Without JavaScript**: Basic features even if JavaScript is off

### 2. Computer Brain (Backend) Speed Tricks
- **Load AI Once**: Start the AI brain when the system starts, keep it running
- **Reuse Connections**: Use the same database connection instead of making new ones
- **Handle Many at Once**: Process multiple orders together efficiently
- **Don't Wait**: Do multiple things at the same time instead of waiting

### 3. AI Brain Speed Tricks
- **Remember Past Choices**: Save what worked before and reuse good ideas
- **Practice Brain**: Use a separate brain for learning to stay stable
- **Try New Things**: Sometimes try random choices to discover better ways
- **Reward Good Work**: Give the AI points for doing what helps the business

---

## Settings and Numbers

### 1. Train Fleet Setup
The system has 6 trains with different sizes:
- **Train 1**: Heavy - can carry 1000 tons
- **Train 2**: Medium - can carry 800 tons
- **Train 3**: Medium - can carry 800 tons
- **Train 4**: Light - can carry 600 tons
- **Train 5**: Light - can carry 600 tons
- **Train 6**: Super Heavy - can carry 1000 tons

### 2. Route Information
Each route has different distances and costs:
- **DAR_KAPIRI**: 1860 km, takes 3 days, 60 ZMW fuel per ton
- **DAR_MBEYA**: 850 km, takes 2 days, 65 ZMW fuel per ton
- **MBEYA_KASAMA**: About 600 km, takes 2 days
- **KAPIRI_NDOLA**: About 400 km, takes 1 day
- **DAR_KIDATU**: About 400 km, takes 1 day
- **KIDATU_TRANS_SHIPMENT**: Special transfer route

### 3. Business Rules
**Priority Levels:**
- **Level 1 (Emergency)**: Handle right away
- **Level 2 (Urgent)**: Handle within 24 hours
- **Level 3 (Priority)**: Handle within 3 days
- **Level 4 (Normal)**: Handle within 7 days
- **Level 5 (Low)**: Handle when possible

**Cost Numbers:**
- **Fuel Costs** (per ton of cargo):
  - Heavy trains: 60 ZMW (more efficient at larger scale)
  - Medium trains: 65 ZMW
  - Light trains: 70 ZMW
  - Super Heavy: 55 ZMW (most efficient)

- **Crew Costs**:
  - Regular crew: 1500 ZMW per train per day
  - Expert crew bonus: 500 ZMW extra
  - Senior crew: 1200 ZMW per train per day

---

## API Connections

### 1. Multi-Route Scheduling
These are the addresses for train scheduling:
- **POST /multi-route/schedule** - Create a new train schedule
- **POST /multi-route/upload-and-schedule** - Upload Excel file and make schedule
- **GET /multi-route/status** - Check system status

### 2. Priority Auto-Scheduling
These are the addresses for automatic priority scheduling:
- **POST /priority/auto-schedule** - Ask AI to make automatic schedule
- **GET /priority/auto-schedule/status** - Check auto-schedule status
- **GET /priority/queue/status** - See how many orders are waiting
- **GET /priority/queue/list** - Get list of waiting orders

### 3. Workflow Integration
These are the addresses for order management:
- **GET /api/workflow/orders** - Get all customer orders
- **POST /api/workflow/orders** - Create new customer order
- **PUT /api/workflow/orders/{id}/assign** - Assign order to a train

---

## Error Handling and Checking

### 1. Input Checking
The system checks everything before processing:

**Frontend Checks:**
- Makes sure there are cargo requirements
- Throws error if no cargo found

**Backend Checks:**
- Checks each route has a valid cargo amount (must be a positive number)
- Throws error if any cargo amount is wrong

### 2. Train Capacity Limits
The system prevents overloading trains:
- Checks each train assignment
- Makes sure cargo doesn't exceed train capacity
- Throws error if a train is overloaded

### 3. Route Validation
The system fixes wrong route names:
- Checks if route is one of the 6 valid TAZARA routes
- If route is invalid, changes it to DAR_KAPIRI (default)
- Shows warning message about the change

---

## Monitoring and Analytics

### 1. Performance Numbers
The system tracks these important numbers:
- **Efficiency Score**: How well we're doing compared to perfect (percentage)
- **Delivery Rate**: How much of customer demand we're meeting (percentage)
- **Cost Efficiency**: How much money we make vs spend (ratio)
- **Utilization Rate**: How much train capacity we're actually using (percentage)

### 2. Real-Time Watching
The system watches things as they happen:
- **Schedule Status**: Whether schedules are active, running, or finished
- **Alerts**: Problems like conflicts, delays, or capacity issues
- **Resource Tracking**: Where trains are and what cargo they're carrying

### 3. History and Trends
The system looks at past performance:
- **Trend Analysis**: How performance changes over time
- **Comparison Reports**: How AI scheduling compares to regular scheduling
- **Cost Analysis**: How operational costs change over time

---

## Future Improvements

### 1. Smarter AI Features
- **Balance Everything**: Consider cost, time, and customer happiness together
- **Predict Future Needs**: Guess how much cargo and trains will be needed
- **Keep Learning**: Get better every day from real operations

### 2. Real-Time Features
- **Live Train Tracking**: Use GPS to see where trains are right now
- **Quick Changes**: Adjust schedules instantly when problems happen
- **Phone Support**: Use mobile phones for field operations

### 3. Connect to Other Systems
- **Business Software**: Connect to company planning systems
- **Customer Website**: Let customers track their orders
- **Partner Systems**: Work with other companies' computers

---

## What This All Means

The TAZARA AI Train Scheduling System is a complete solution for running trains better, using:

- **Smart Rules** for predictable, reliable scheduling
- **Learning AI** that gets better with experience
- **Priority System** that puts important customers first
- **Money Saving** that reduces costs and increases profits

The system handles complex train scheduling across many routes while keeping operations efficient and customers happy. The design allows for continuous improvements and changes as business needs evolve.

---

*Document written: May 7, 2026*
*System version: 3.0.0*
*Based on current system analysis*
