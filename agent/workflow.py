"""
OMNICUS Workflow Engine Module
==============================
Orchestration engine for trading workflows and decision pipelines.

This module coordinates the flow of trading decisions from
market analysis through execution and learning.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Awaitable
from enum import Enum
import asyncio
import time
from collections import deque


class WorkflowState(Enum):
    """States of a workflow"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowType(Enum):
    """Types of trading workflows"""
    MARKET_SCAN = "market_scan"           # Scan for opportunities
    TRADE_ANALYSIS = "trade_analysis"     # Analyze a potential trade
    TRADE_EXECUTION = "trade_execution"   # Execute a trade
    POSITION_MANAGEMENT = "position_mgmt" # Manage existing positions
    RISK_CHECK = "risk_check"             # Risk assessment workflow
    LEARNING_CYCLE = "learning_cycle"     # Learn from completed trades
    DAILY_ROUTINE = "daily_routine"       # Daily startup routine


class StepStatus(Enum):
    """Status of a workflow step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    
    name: str
    action: Callable
    description: str = ""
    required: bool = True
    timeout_seconds: float = 30.0
    
    # Execution state
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    async def execute(self, context: Dict) -> bool:
        """
        Execute this step
        
        Args:
            context: Workflow context dictionary
            
        Returns:
            True if successful
        """
        self.status = StepStatus.IN_PROGRESS
        self.start_time = datetime.now()
        
        try:
            # Handle both sync and async functions
            if asyncio.iscoroutinefunction(self.action):
                self.result = await asyncio.wait_for(
                    self.action(context),
                    timeout=self.timeout_seconds
                )
            else:
                self.result = self.action(context)
            
            self.status = StepStatus.COMPLETED
            self.end_time = datetime.now()
            return True
            
        except asyncio.TimeoutError:
            self.status = StepStatus.FAILED
            self.error = f"Step timed out after {self.timeout_seconds}s"
            self.end_time = datetime.now()
            return False
            
        except Exception as e:
            self.status = StepStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.now()
            return False
    
    @property
    def duration_ms(self) -> float:
        """Calculate step duration in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "result": str(self.result) if self.result else None,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "required": self.required
        }


@dataclass
class Workflow:
    """
    A trading workflow - a sequence of steps to accomplish a task
    
    Workflows are the backbone of OMNICUS's operation. They define
    how trading decisions flow from analysis to execution to learning.
    """
    
    workflow_id: str
    workflow_type: WorkflowType
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Workflow state
    state: WorkflowState = WorkflowState.PENDING
    current_step: int = 0
    context: Dict = field(default_factory=dict)
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Callbacks
    on_complete: Optional[Callable] = None
    on_fail: Optional[Callable] = None
    
    def add_step(self, step: WorkflowStep) -> "Workflow":
        """Add a step to the workflow"""
        self.steps.append(step)
        return self
    
    async def run(self) -> Dict:
        """
        Execute the workflow
        
        Returns:
            Final workflow result
        """
        self.state = WorkflowState.RUNNING
        self.started_at = datetime.now()
        
        for i, step in enumerate(self.steps):
            self.current_step = i
            
            success = await step.execute(self.context)
            
            if not success and step.required:
                # Required step failed - abort workflow
                self.state = WorkflowState.FAILED
                self.completed_at = datetime.now()
                
                if self.on_fail:
                    await self._call_callback(self.on_fail)
                
                return self._build_result()
            
            # Store step result in context
            self.context[f"step_{step.name}_result"] = step.result
        
        # All steps completed
        self.state = WorkflowState.COMPLETED
        self.completed_at = datetime.now()
        
        if self.on_complete:
            await self._call_callback(self.on_complete)
        
        return self._build_result()
    
    async def _call_callback(self, callback: Callable):
        """Call a callback function"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(self)
            else:
                callback(self)
        except Exception as e:
            pass  # Don't let callback errors break workflow
    
    def _build_result(self) -> Dict:
        """Build the final result dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "state": self.state.value,
            "steps_completed": sum(1 for s in self.steps if s.status == StepStatus.COMPLETED),
            "steps_failed": sum(1 for s in self.steps if s.status == StepStatus.FAILED),
            "total_steps": len(self.steps),
            "duration_ms": self.duration_ms,
            "context": self.context,
            "steps": [s.to_dict() for s in self.steps]
        }
    
    @property
    def duration_ms(self) -> float:
        """Calculate total workflow duration"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0
    
    def pause(self):
        """Pause the workflow"""
        if self.state == WorkflowState.RUNNING:
            self.state = WorkflowState.PAUSED
    
    def resume(self):
        """Resume a paused workflow"""
        if self.state == WorkflowState.PAUSED:
            self.state = WorkflowState.RUNNING
    
    def cancel(self):
        """Cancel the workflow"""
        self.state = WorkflowState.CANCELLED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type.value,
            "description": self.description,
            "state": self.state.value,
            "current_step": self.current_step,
            "total_steps": len(self.steps),
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms
        }


class WorkflowEngine:
    """
    Central orchestration engine for OMNICUS trading workflows
    
    The Workflow Engine manages the entire lifecycle of trading decisions:
    - Market scanning workflows
    - Trade analysis workflows  
    - Execution workflows
    - Learning workflows
    
    It coordinates between the Brain, Soul, Skills, and Tools to
    make cohesive, well-reasoned trading decisions.
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize the workflow engine
        
        Args:
            max_concurrent: Maximum concurrent workflows
        """
        self.max_concurrent = max_concurrent
        
        # Active workflows
        self._active_workflows: Dict[str, Workflow] = {}
        self._workflow_queue: deque = deque()
        
        # Workflow history
        self._completed_workflows: List[Dict] = []
        self._max_history = 1000
        
        # Workflow templates
        self._templates: Dict[str, Workflow] = {}
        
        # Event handlers
        self._handlers: Dict[str, List[Callable]] = {
            "workflow_start": [],
            "workflow_complete": [],
            "workflow_fail": [],
            "step_complete": [],
        }
        
        # Initialize default templates
        self._init_default_templates()
    
    def _init_default_templates(self):
        """Initialize default workflow templates"""
        
        # Market Scan Workflow Template
        scan_template = Workflow(
            workflow_id="template_market_scan",
            workflow_type=WorkflowType.MARKET_SCAN,
            description="Scan markets for trading opportunities"
        )
        scan_template.add_step(WorkflowStep(
            name="fetch_market_data",
            action=self._fetch_market_data,
            description="Fetch current market data for all symbols"
        ))
        scan_template.add_step(WorkflowStep(
            name="analyze_technicals",
            action=self._analyze_technicals,
            description="Calculate technical indicators"
        ))
        scan_template.add_step(WorkflowStep(
            name="detect_patterns",
            action=self._detect_patterns,
            description="Detect chart patterns"
        ))
        scan_template.add_step(WorkflowStep(
            name="score_opportunities",
            action=self._score_opportunities,
            description="Score and rank opportunities"
        ))
        self._templates["market_scan"] = scan_template
        
        # Trade Analysis Workflow Template
        analysis_template = Workflow(
            workflow_id="template_trade_analysis",
            workflow_type=WorkflowType.TRADE_ANALYSIS,
            description="Analyze a potential trade"
        )
        analysis_template.add_step(WorkflowStep(
            name="gather_data",
            action=self._gather_trade_data,
            description="Gather all relevant data for trade"
        ))
        analysis_template.add_step(WorkflowStep(
            name="technical_analysis",
            action=self._perform_technical_analysis,
            description="Perform technical analysis"
        ))
        analysis_template.add_step(WorkflowStep(
            name="risk_assessment",
            action=self._assess_trade_risk,
            description="Assess risk for potential trade"
        ))
        analysis_template.add_step(WorkflowStep(
            name="calculate_position",
            action=self._calculate_position,
            description="Calculate position size and levels"
        ))
        analysis_template.add_step(WorkflowStep(
            name="generate_decision",
            action=self._generate_trade_decision,
            description="Generate final trade decision"
        ))
        self._templates["trade_analysis"] = analysis_template
        
        # Trade Execution Workflow Template
        execution_template = Workflow(
            workflow_id="template_trade_execution",
            workflow_type=WorkflowType.TRADE_EXECUTION,
            description="Execute a trade"
        )
        execution_template.add_step(WorkflowStep(
            name="validate_signal",
            action=self._validate_signal,
            description="Validate the trade signal"
        ))
        execution_template.add_step(WorkflowStep(
            name="check_risk_limits",
            action=self._check_risk_limits,
            description="Check against risk limits"
        ))
        execution_template.add_step(WorkflowStep(
            name="place_order",
            action=self._place_order,
            description="Place the trade order"
        ))
        execution_template.add_step(WorkflowStep(
            name="set_stops",
            action=self._set_stop_loss,
            description="Set stop loss and take profit"
        ))
        execution_template.add_step(WorkflowStep(
            name="record_trade",
            action=self._record_trade,
            description="Record trade in memory bank"
        ))
        self._templates["trade_execution"] = execution_template
        
        # Learning Cycle Workflow Template
        learning_template = Workflow(
            workflow_id="template_learning_cycle",
            workflow_type=WorkflowType.LEARNING_CYCLE,
            description="Learn from completed trade"
        )
        learning_template.add_step(WorkflowStep(
            name="analyze_outcome",
            action=self._analyze_trade_outcome,
            description="Analyze trade outcome"
        ))
        learning_template.add_step(WorkflowStep(
            name="update_skills",
            action=self._update_skills,
            description="Update skill accuracy"
        ))
        learning_template.add_step(WorkflowStep(
            name="extract_lessons",
            action=self._extract_lessons,
            description="Extract lessons from trade"
        ))
        learning_template.add_step(WorkflowStep(
            name="update_memory",
            action=self._update_memory,
            description="Store memory in bank"
        ))
        self._templates["learning_cycle"] = learning_template
    
    # Default step actions (can be overridden)
    async def _fetch_market_data(self, context: Dict) -> Dict:
        """Fetch market data - override with real implementation"""
        return {"status": "success", "symbols": context.get("symbols", [])}
    
    async def _analyze_technicals(self, context: Dict) -> Dict:
        """Analyze technicals - override with real implementation"""
        return {"status": "success", "indicators": {}}
    
    async def _detect_patterns(self, context: Dict) -> Dict:
        """Detect patterns - override with real implementation"""
        return {"status": "success", "patterns": []}
    
    async def _score_opportunities(self, context: Dict) -> Dict:
        """Score opportunities - override with real implementation"""
        return {"status": "success", "scores": []}
    
    async def _gather_trade_data(self, context: Dict) -> Dict:
        """Gather trade data - override with real implementation"""
        return {"status": "success", "data": {}}
    
    async def _perform_technical_analysis(self, context: Dict) -> Dict:
        """Perform technical analysis - override with real implementation"""
        return {"status": "success", "analysis": {}}
    
    async def _assess_trade_risk(self, context: Dict) -> Dict:
        """Assess trade risk - override with real implementation"""
        return {"status": "success", "risk": {}}
    
    async def _calculate_position(self, context: Dict) -> Dict:
        """Calculate position - override with real implementation"""
        return {"status": "success", "position": {}}
    
    async def _generate_trade_decision(self, context: Dict) -> Dict:
        """Generate trade decision - override with real implementation"""
        return {"status": "success", "decision": {}}
    
    async def _validate_signal(self, context: Dict) -> Dict:
        """Validate signal - override with real implementation"""
        return {"status": "success", "valid": True}
    
    async def _check_risk_limits(self, context: Dict) -> Dict:
        """Check risk limits - override with real implementation"""
        return {"status": "success", "within_limits": True}
    
    async def _place_order(self, context: Dict) -> Dict:
        """Place order - override with real implementation"""
        return {"status": "success", "order_id": "mock_order"}
    
    async def _set_stop_loss(self, context: Dict) -> Dict:
        """Set stop loss - override with real implementation"""
        return {"status": "success", "stop_set": True}
    
    async def _record_trade(self, context: Dict) -> Dict:
        """Record trade - override with real implementation"""
        return {"status": "success", "recorded": True}
    
    async def _analyze_trade_outcome(self, context: Dict) -> Dict:
        """Analyze trade outcome - override with real implementation"""
        return {"status": "success", "outcome": {}}
    
    async def _update_skills(self, context: Dict) -> Dict:
        """Update skills - override with real implementation"""
        return {"status": "success", "skills_updated": []}
    
    async def _extract_lessons(self, context: Dict) -> Dict:
        """Extract lessons - override with real implementation"""
        return {"status": "success", "lessons": []}
    
    async def _update_memory(self, context: Dict) -> Dict:
        """Update memory - override with real implementation"""
        return {"status": "success", "memory_stored": True}
    
    def create_workflow(
        self, 
        workflow_type: str, 
        context: Dict = None,
        custom_steps: List[WorkflowStep] = None
    ) -> Workflow:
        """
        Create a new workflow from a template
        
        Args:
            workflow_type: Type of workflow to create
            context: Initial context
            custom_steps: Custom steps (overrides template)
            
        Returns:
            The created workflow
        """
        template = self._templates.get(workflow_type)
        
        if not template:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        # Create new workflow from template
        workflow = Workflow(
            workflow_id=f"{workflow_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            workflow_type=template.workflow_type,
            description=template.description,
            context=context or {},
        )
        
        # Copy steps from template or use custom
        if custom_steps:
            for step in custom_steps:
                workflow.add_step(step)
        else:
            for step in template.steps:
                workflow.add_step(WorkflowStep(
                    name=step.name,
                    action=step.action,
                    description=step.description,
                    required=step.required,
                    timeout_seconds=step.timeout_seconds
                ))
        
        return workflow
    
    def register_template(self, name: str, workflow: Workflow):
        """
        Register a custom workflow template
        
        Args:
            name: Template name
            workflow: Workflow to use as template
        """
        self._templates[name] = workflow
    
    async def execute_workflow(self, workflow: Workflow) -> Dict:
        """
        Execute a workflow
        
        Args:
            workflow: Workflow to execute
            
        Returns:
            Workflow result
        """
        # Add to active workflows
        self._active_workflows[workflow.workflow_id] = workflow
        
        # Notify handlers
        await self._notify_handlers("workflow_start", workflow)
        
        # Run the workflow
        result = await workflow.run()
        
        # Move to history
        del self._active_workflows[workflow.workflow_id]
        self._completed_workflows.append(result)
        
        # Trim history if needed
        if len(self._completed_workflows) > self._max_history:
            self._completed_workflows = self._completed_workflows[-self._max_history:]
        
        # Notify handlers
        if workflow.state == WorkflowState.COMPLETED:
            await self._notify_handlers("workflow_complete", workflow)
        else:
            await self._notify_handlers("workflow_fail", workflow)
        
        return result
    
    async def execute_workflow_async(self, workflow: Workflow) -> str:
        """
        Execute a workflow asynchronously (returns immediately)
        
        Args:
            workflow: Workflow to execute
            
        Returns:
            Workflow ID
        """
        self._workflow_queue.append(workflow)
        
        # Start processing if not at capacity
        if len(self._active_workflows) < self.max_concurrent:
            asyncio.create_task(self._process_queue())
        
        return workflow.workflow_id
    
    async def _process_queue(self):
        """Process queued workflows"""
        while self._workflow_queue and len(self._active_workflows) < self.max_concurrent:
            workflow = self._workflow_queue.popleft()
            await self.execute_workflow(workflow)
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """
        Get status of a workflow
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow status dict or None
        """
        if workflow_id in self._active_workflows:
            return self._active_workflows[workflow_id].to_dict()
        
        # Check history
        for result in self._completed_workflows:
            if result["workflow_id"] == workflow_id:
                return result
        
        return None
    
    def register_handler(self, event: str, handler: Callable):
        """
        Register an event handler
        
        Args:
            event: Event name (workflow_start, workflow_complete, workflow_fail, step_complete)
            handler: Async or sync function to call
        """
        if event in self._handlers:
            self._handlers[event].append(handler)
    
    async def _notify_handlers(self, event: str, workflow: Workflow):
        """Notify all handlers of an event"""
        for handler in self._handlers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(workflow)
                else:
                    handler(workflow)
            except Exception as e:
                pass  # Don't let handler errors break workflow
    
    def get_active_workflows(self) -> List[Dict]:
        """Get all active workflows"""
        return [w.to_dict() for w in self._active_workflows.values()]
    
    def get_workflow_stats(self) -> Dict:
        """Get workflow engine statistics"""
        total_completed = len(self._completed_workflows)
        successful = sum(
            1 for r in self._completed_workflows 
            if r["state"] == "completed"
        )
        
        return {
            "active_workflows": len(self._active_workflows),
            "queued_workflows": len(self._workflow_queue),
            "total_completed": total_completed,
            "successful_completed": successful,
            "success_rate": successful / total_completed if total_completed > 0 else 0,
            "available_templates": list(self._templates.keys()),
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """
        Cancel an active workflow
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            True if cancelled
        """
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].cancel()
            return True
        return False
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """Pause an active workflow"""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].pause()
            return True
        return False
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """Resume a paused workflow"""
        if workflow_id in self._active_workflows:
            self._active_workflows[workflow_id].resume()
            return True
        return False


# Default workflow engine instance
workflow_engine = WorkflowEngine()
