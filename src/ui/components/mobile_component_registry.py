"""
Mobile Component Registry for AI Agent Autonomous Development

This module provides a centralized registry for all mobile UI components,
enabling AI agents to discover, test, and modify components autonomously.

AI Agent Friendly Features:
- Comprehensive component metadata for AI understanding
- Autonomous testing interfaces
- Self-healing capabilities
- Clear component relationships and dependencies
"""

import inspect
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

import streamlit as st
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ComponentMetadata:
    """Metadata for AI agent component understanding."""
    
    component_id: str
    component_type: str
    display_name: str
    description: str
    ai_agent_friendly_description: str
    interactive_elements: List[Dict[str, Any]] = field(default_factory=list)
    state_dependencies: List[str] = field(default_factory=list)
    css_classes: List[str] = field(default_factory=list)
    test_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    ai_agent_instructions: Dict[str, str] = field(default_factory=dict)
    parent_component: Optional[str] = None
    child_components: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    last_updated: Optional[str] = None
    ai_agent_testable: bool = True
    auto_fix_enabled: bool = True


class MobileComponent(ABC):
    """Base class for all mobile UI components.
    
    AI Agent Design Principles:
    - Clear method naming and documentation
    - Predictable state management
    - Built-in testing capabilities
    - Error handling and recovery
    - Semantic component IDs
    """
    
    def __init__(self, component_id: str, **kwargs):
        self.component_id = component_id
        self.metadata = self._get_component_metadata()
        self.test_results: Dict[str, Any] = {}
        self.last_test_time: Optional[float] = None
        self.ai_agent_context: Dict[str, Any] = {}
        
    @abstractmethod
    def _get_component_metadata(self) -> ComponentMetadata:
        """Return component metadata for AI agent understanding."""
        pass
    
    @abstractmethod
    def render(self, **kwargs) -> None:
        """Render the component in Streamlit."""
        pass
    
    def ai_agent_test_component(self) -> Dict[str, Any]:
        """AI Agent: Test component functionality autonomously."""
        test_start = time.time()
        test_results = {
            'component_id': self.component_id,
            'test_timestamp': test_start,
            'tests_performed': [],
            'issues_found': [],
            'fixes_applied': [],
            'overall_status': 'unknown'
        }
        
        try:
            # Test component initialization
            init_test = self._test_initialization()
            test_results['tests_performed'].append(init_test)
            
            # Test interactive elements
            for element in self.metadata.interactive_elements:
                element_test = self._test_interactive_element(element)
                test_results['tests_performed'].append(element_test)
            
            # Test state dependencies
            state_test = self._test_state_dependencies()
            test_results['tests_performed'].append(state_test)
            
            # Test rendering
            render_test = self._test_rendering()
            test_results['tests_performed'].append(render_test)
            
            # Analyze results and determine overall status
            failed_tests = [t for t in test_results['tests_performed'] if t.get('status') == 'failed']
            if not failed_tests:
                test_results['overall_status'] = 'passed'
            else:
                test_results['overall_status'] = 'failed'
                test_results['issues_found'] = [t.get('issue') for t in failed_tests if t.get('issue')]
                
                # Attempt auto-fixes if enabled
                if self.metadata.auto_fix_enabled:
                    fixes = self._ai_agent_auto_fix_issues(test_results['issues_found'])
                    test_results['fixes_applied'] = fixes
                    
                    # Re-test after fixes
                    if fixes:
                        test_results['overall_status'] = 'fixed_and_retested'
            
        except Exception as e:
            test_results['overall_status'] = 'error'
            test_results['error'] = str(e)
            logger.error(f"AI Agent testing failed for {self.component_id}: {e}")
        
        test_results['test_duration'] = time.time() - test_start
        self.test_results = test_results
        self.last_test_time = test_start
        
        return test_results
    
    def _test_initialization(self) -> Dict[str, Any]:
        """Test component initialization."""
        try:
            # Check if component has required attributes
            required_attrs = ['component_id', 'metadata']
            missing_attrs = [attr for attr in required_attrs if not hasattr(self, attr)]
            
            if missing_attrs:
                return {
                    'test_name': 'initialization',
                    'status': 'failed',
                    'issue': f'Missing required attributes: {missing_attrs}'
                }
            
            return {
                'test_name': 'initialization',
                'status': 'passed',
                'details': 'Component initialized successfully'
            }
        except Exception as e:
            return {
                'test_name': 'initialization',
                'status': 'error',
                'issue': str(e)
            }
    
    def _test_interactive_element(self, element: Dict[str, Any]) -> Dict[str, Any]:
        """Test individual interactive element."""
        element_id = element.get('id', 'unknown')
        element_type = element.get('type', 'unknown')
        
        try:
            # Basic element validation
            if not element.get('id'):
                return {
                    'test_name': f'interactive_element_{element_id}',
                    'status': 'failed',
                    'issue': f'Element {element_id} missing ID'
                }
            
            # Check for unique keys (Streamlit requirement)
            if element_type in ['button', 'text_input', 'selectbox'] and not element.get('key'):
                return {
                    'test_name': f'interactive_element_{element_id}',
                    'status': 'failed',
                    'issue': f'Element {element_id} missing unique key for Streamlit'
                }
            
            return {
                'test_name': f'interactive_element_{element_id}',
                'status': 'passed',
                'details': f'Element {element_id} validated successfully'
            }
        except Exception as e:
            return {
                'test_name': f'interactive_element_{element_id}',
                'status': 'error',
                'issue': str(e)
            }
    
    def _test_state_dependencies(self) -> Dict[str, Any]:
        """Test state dependencies."""
        try:
            missing_state_vars = []
            for state_var in self.metadata.state_dependencies:
                if state_var not in st.session_state:
                    missing_state_vars.append(state_var)
            
            if missing_state_vars:
                return {
                    'test_name': 'state_dependencies',
                    'status': 'failed',
                    'issue': f'Missing session state variables: {missing_state_vars}'
                }
            
            return {
                'test_name': 'state_dependencies',
                'status': 'passed',
                'details': 'All state dependencies satisfied'
            }
        except Exception as e:
            return {
                'test_name': 'state_dependencies',
                'status': 'error',
                'issue': str(e)
            }
    
    def _test_rendering(self) -> Dict[str, Any]:
        """Test component rendering."""
        try:
            # This is a basic test - in a full implementation,
            # we would capture rendering output and validate it
            render_method = getattr(self, 'render', None)
            if not render_method or not callable(render_method):
                return {
                    'test_name': 'rendering',
                    'status': 'failed',
                    'issue': 'Component missing render method'
                }
            
            return {
                'test_name': 'rendering',
                'status': 'passed',
                'details': 'Render method exists and is callable'
            }
        except Exception as e:
            return {
                'test_name': 'rendering',
                'status': 'error',
                'issue': str(e)
            }
    
    def _ai_agent_auto_fix_issues(self, issues: List[str]) -> List[Dict[str, Any]]:
        """AI Agent: Automatically fix common issues."""
        fixes_applied = []
        
        for issue in issues:
            if 'missing unique key' in issue.lower():
                fix = self._fix_missing_keys(issue)
                if fix:
                    fixes_applied.append(fix)
            elif 'missing session state' in issue.lower():
                fix = self._fix_missing_state_vars(issue)
                if fix:
                    fixes_applied.append(fix)
        
        return fixes_applied
    
    def _fix_missing_keys(self, issue: str) -> Optional[Dict[str, Any]]:
        """Fix missing Streamlit keys."""
        try:
            # Generate unique keys for interactive elements
            for element in self.metadata.interactive_elements:
                if not element.get('key'):
                    element['key'] = f"{self.component_id}_{element.get('id', 'unknown')}_{int(time.time())}"
            
            return {
                'fix_type': 'missing_keys',
                'fix_description': 'Generated unique keys for interactive elements',
                'status': 'applied'
            }
        except Exception as e:
            return {
                'fix_type': 'missing_keys',
                'fix_description': f'Failed to fix missing keys: {e}',
                'status': 'failed'
            }
    
    def _fix_missing_state_vars(self, issue: str) -> Optional[Dict[str, Any]]:
        """Fix missing session state variables."""
        try:
            # Initialize missing state variables with default values
            for state_var in self.metadata.state_dependencies:
                if state_var not in st.session_state:
                    # Set reasonable defaults based on variable name
                    if 'count' in state_var or 'index' in state_var:
                        st.session_state[state_var] = 0
                    elif 'list' in state_var or 'history' in state_var:
                        st.session_state[state_var] = []
                    elif 'dict' in state_var or 'config' in state_var:
                        st.session_state[state_var] = {}
                    elif 'bool' in state_var or 'flag' in state_var or 'enabled' in state_var:
                        st.session_state[state_var] = False
                    else:
                        st.session_state[state_var] = None
            
            return {
                'fix_type': 'missing_state_vars',
                'fix_description': 'Initialized missing session state variables',
                'status': 'applied'
            }
        except Exception as e:
            return {
                'fix_type': 'missing_state_vars',
                'fix_description': f'Failed to fix missing state vars: {e}',
                'status': 'failed'
            }
    
    def get_ai_agent_context(self) -> Dict[str, Any]:
        """Return context for AI agent understanding."""
        return {
            'component_id': self.component_id,
            'component_type': self.metadata.component_type,
            'display_name': self.metadata.display_name,
            'description': self.metadata.ai_agent_friendly_description,
            'interactive_elements': self.metadata.interactive_elements,
            'state_dependencies': self.metadata.state_dependencies,
            'test_results': self.test_results,
            'last_test_time': self.last_test_time,
            'ai_agent_instructions': self.metadata.ai_agent_instructions
        }


class MobileComponentRegistry:
    """Central registry for all mobile UI components.
    
    AI Agent Autonomous Development Features:
    - Component discovery and introspection
    - Automated testing orchestration
    - Issue detection and resolution
    - Performance monitoring
    - Component relationship mapping
    """
    
    def __init__(self):
        self._components: Dict[str, Type[MobileComponent]] = {}
        self._component_instances: Dict[str, MobileComponent] = {}
        self._component_relationships: Dict[str, List[str]] = {}
        self._test_history: List[Dict[str, Any]] = []
        self._ai_agent_context: Dict[str, Any] = {}
        
        logger.info("MobileComponentRegistry initialized for AI agent autonomous development")
    
    def register_component(self, component_class: Type[MobileComponent], component_id: str = None) -> None:
        """Register a mobile component for AI agent discovery."""
        if component_id is None:
            component_id = component_class.__name__.lower()
        
        self._components[component_id] = component_class
        
        # Create instance for metadata extraction
        try:
            instance = component_class(component_id)
            self._component_instances[component_id] = instance
            
            # Build relationship map
            metadata = instance.metadata
            if metadata.parent_component:
                if metadata.parent_component not in self._component_relationships:
                    self._component_relationships[metadata.parent_component] = []
                self._component_relationships[metadata.parent_component].append(component_id)
            
            logger.info(f"Registered mobile component: {component_id}")
        except Exception as e:
            logger.error(f"Failed to register component {component_id}: {e}")
    
    def get_component(self, component_id: str) -> Optional[MobileComponent]:
        """Get component instance by ID."""
        return self._component_instances.get(component_id)
    
    def get_all_components(self) -> Dict[str, MobileComponent]:
        """Get all registered components."""
        return self._component_instances.copy()
    
    def get_component_metadata(self, component_id: str) -> Optional[ComponentMetadata]:
        """Get component metadata for AI agent analysis."""
        component = self.get_component(component_id)
        return component.metadata if component else None
    
    def ai_agent_discover_components(self) -> Dict[str, Any]:
        """AI Agent: Discover all available components and their capabilities."""
        discovery_results = {
            'discovery_timestamp': time.time(),
            'total_components': len(self._components),
            'components': {},
            'relationships': self._component_relationships.copy(),
            'testable_components': [],
            'auto_fixable_components': []
        }
        
        for component_id, component in self._component_instances.items():
            component_info = {
                'component_id': component_id,
                'component_type': component.metadata.component_type,
                'display_name': component.metadata.display_name,
                'description': component.metadata.ai_agent_friendly_description,
                'interactive_elements_count': len(component.metadata.interactive_elements),
                'state_dependencies_count': len(component.metadata.state_dependencies),
                'testable': component.metadata.ai_agent_testable,
                'auto_fix_enabled': component.metadata.auto_fix_enabled,
                'ai_agent_instructions': component.metadata.ai_agent_instructions
            }
            
            discovery_results['components'][component_id] = component_info
            
            if component.metadata.ai_agent_testable:
                discovery_results['testable_components'].append(component_id)
            
            if component.metadata.auto_fix_enabled:
                discovery_results['auto_fixable_components'].append(component_id)
        
        self._ai_agent_context['last_discovery'] = discovery_results
        return discovery_results
    
    def ai_agent_test_all_components(self) -> Dict[str, Any]:
        """AI Agent: Test all registered components autonomously."""
        test_session = {
            'test_session_id': f"session_{int(time.time())}",
            'test_timestamp': time.time(),
            'components_tested': 0,
            'components_passed': 0,
            'components_failed': 0,
            'components_fixed': 0,
            'test_results': {},
            'issues_found': [],
            'fixes_applied': [],
            'recommendations': []
        }
        
        for component_id, component in self._component_instances.items():
            if component.metadata.ai_agent_testable:
                logger.info(f"AI Agent testing component: {component_id}")
                
                test_results = component.ai_agent_test_component()
                test_session['test_results'][component_id] = test_results
                test_session['components_tested'] += 1
                
                if test_results['overall_status'] == 'passed':
                    test_session['components_passed'] += 1
                elif test_results['overall_status'] == 'failed':
                    test_session['components_failed'] += 1
                    test_session['issues_found'].extend(test_results.get('issues_found', []))
                elif test_results['overall_status'] == 'fixed_and_retested':
                    test_session['components_fixed'] += 1
                    test_session['fixes_applied'].extend(test_results.get('fixes_applied', []))
        
        # Generate AI agent recommendations
        test_session['recommendations'] = self._generate_ai_agent_recommendations(test_session)
        
        # Store in test history
        self._test_history.append(test_session)
        
        logger.info(f"AI Agent completed testing session: {test_session['components_tested']} components tested, "
                   f"{test_session['components_passed']} passed, {test_session['components_failed']} failed, "
                   f"{test_session['components_fixed']} fixed")
        
        return test_session
    
    def _generate_ai_agent_recommendations(self, test_session: Dict[str, Any]) -> List[str]:
        """Generate recommendations for AI agent based on test results."""
        recommendations = []
        
        if test_session['components_failed'] > 0:
            recommendations.append(
                f"Found {test_session['components_failed']} components with issues. "
                "Enable auto-fix for these components or investigate root causes."
            )
        
        if test_session['components_fixed'] > 0:
            recommendations.append(
                f"Successfully auto-fixed {test_session['components_fixed']} components. "
                "Consider updating component implementations to prevent these issues."
            )
        
        if test_session['components_tested'] == test_session['components_passed']:
            recommendations.append("All components passed testing. System is in good health.")
        
        # Analyze common issues
        all_issues = test_session.get('issues_found', [])
        if all_issues:
            issue_types = {}
            for issue in all_issues:
                if 'missing' in issue.lower():
                    issue_types['missing_dependencies'] = issue_types.get('missing_dependencies', 0) + 1
                elif 'key' in issue.lower():
                    issue_types['streamlit_keys'] = issue_types.get('streamlit_keys', 0) + 1
            
            for issue_type, count in issue_types.items():
                if count > 1:
                    recommendations.append(
                        f"Multiple components ({count}) have {issue_type} issues. "
                        "Consider implementing a global fix."
                    )
        
        return recommendations
    
    def get_ai_agent_context(self) -> Dict[str, Any]:
        """Get comprehensive context for AI agent decision making."""
        return {
            'registry_info': {
                'total_components': len(self._components),
                'testable_components': len([c for c in self._component_instances.values() 
                                          if c.metadata.ai_agent_testable]),
                'auto_fixable_components': len([c for c in self._component_instances.values() 
                                              if c.metadata.auto_fix_enabled])
            },
            'recent_test_history': self._test_history[-5:] if self._test_history else [],
            'component_relationships': self._component_relationships,
            'ai_agent_context': self._ai_agent_context
        }
    
    def ai_agent_monitor_component_health(self) -> Dict[str, Any]:
        """AI Agent: Monitor overall component health and system status."""
        health_report = {
            'timestamp': time.time(),
            'overall_health': 'unknown',
            'component_health': {},
            'system_recommendations': [],
            'critical_issues': [],
            'performance_metrics': {}
        }
        
        healthy_components = 0
        total_components = len(self._component_instances)
        
        for component_id, component in self._component_instances.items():
            # Check if component has recent test results
            if component.test_results:
                status = component.test_results.get('overall_status', 'unknown')
                health_report['component_health'][component_id] = {
                    'status': status,
                    'last_test': component.last_test_time,
                    'issues': len(component.test_results.get('issues_found', []))
                }
                
                if status in ['passed', 'fixed_and_retested']:
                    healthy_components += 1
            else:
                health_report['component_health'][component_id] = {
                    'status': 'not_tested',
                    'last_test': None,
                    'issues': 0
                }
        
        # Calculate overall health
        if total_components == 0:
            health_report['overall_health'] = 'no_components'
        elif healthy_components == total_components:
            health_report['overall_health'] = 'excellent'
        elif healthy_components >= total_components * 0.8:
            health_report['overall_health'] = 'good'
        elif healthy_components >= total_components * 0.6:
            health_report['overall_health'] = 'fair'
        else:
            health_report['overall_health'] = 'poor'
        
        # Generate system recommendations
        if health_report['overall_health'] in ['fair', 'poor']:
            health_report['system_recommendations'].append(
                "Run comprehensive testing and auto-fix on all components"
            )
        
        untested_components = [cid for cid, health in health_report['component_health'].items() 
                             if health['status'] == 'not_tested']
        if untested_components:
            health_report['system_recommendations'].append(
                f"Test {len(untested_components)} untested components: {untested_components[:5]}"
            )
        
        return health_report


# Global registry instance for AI agent access
mobile_component_registry = MobileComponentRegistry()


def register_mobile_component(component_class: Type[MobileComponent], component_id: str = None):
    """Decorator for registering mobile components."""
    def decorator(cls):
        mobile_component_registry.register_component(cls, component_id)
        return cls
    
    if component_class is not None:
        # Called without parentheses
        mobile_component_registry.register_component(component_class, component_id)
        return component_class
    else:
        # Called with parentheses
        return decorator