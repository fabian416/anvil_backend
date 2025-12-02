#!/usr/bin/env python3
"""
Comprehensive Backend Implementation Analysis Tool
Analyzes all backend implementations and maps to frontend documentation.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class APIEndpoint:
    """Represents an API endpoint."""
    method: str
    path: str
    file_path: str
    line_number: int
    handler_name: str = ""


@dataclass
class BackendFeature:
    """Represents a backend feature/module."""
    name: str
    application_modules: List[str] = field(default_factory=list)
    domain_entities: List[str] = field(default_factory=list)
    api_endpoints: List[APIEndpoint] = field(default_factory=list)
    routers: List[str] = field(default_factory=list)
    has_websocket: bool = False


class BackendAnalyzer:
    """Analyzes backend implementation comprehensively."""
    
    def __init__(self, backend_root: Path):
        self.backend_root = backend_root
        self.src_root = backend_root / "src" / "app"
        self.features: Dict[str, BackendFeature] = {}
        
    def analyze(self):
        """Run complete analysis."""
        print("🔍 Starting Comprehensive Backend Analysis...")
        print(f"📂 Backend Root: {self.backend_root}\n")
        
        # 1. Analyze domain entities
        print("📊 Analyzing Domain Entities...")
        entities = self.analyze_domain_entities()
        print(f"   Found {len(entities)} domain entities\n")
        
        # 2. Analyze application modules
        print("📊 Analyzing Application Modules...")
        app_modules = self.analyze_application_modules()
        print(f"   Found {len(app_modules)} application modules\n")
        
        # 3. Analyze API routers
        print("📊 Analyzing API Routers...")
        routers = self.analyze_routers()
        print(f"   Found {len(routers)} routers\n")
        
        # 4. Extract API endpoints
        print("📊 Extracting API Endpoints...")
        endpoints = self.extract_all_endpoints()
        print(f"   Found {len(endpoints)} API endpoints\n")
        
        # 5. Map features
        print("📊 Mapping Features...")
        self.map_features(entities, app_modules, routers, endpoints)
        print(f"   Identified {len(self.features)} features\n")
        
        return self.generate_report()
    
    def analyze_domain_entities(self) -> List[str]:
        """Analyze domain entities."""
        entities_dir = self.src_root / "domain" / "entities"
        entities = []
        
        for file_path in entities_dir.rglob("*.py"):
            if file_path.name != "__init__.py" and "__pycache__" not in str(file_path):
                rel_path = file_path.relative_to(entities_dir)
                entities.append(str(rel_path).replace(".py", "").replace("/", "."))
        
        return sorted(entities)
    
    def analyze_application_modules(self) -> List[str]:
        """Analyze application layer modules."""
        app_dir = self.src_root / "application"
        modules = []
        
        for item in app_dir.iterdir():
            if item.is_dir() and not item.name.startswith("_"):
                modules.append(item.name)
        
        return sorted(modules)
    
    def analyze_routers(self) -> List[str]:
        """Analyze API routers."""
        controllers_dir = self.src_root / "presentation" / "http" / "controllers"
        routers = []
        
        for file_path in controllers_dir.rglob("*router*.py"):
            if "__pycache__" not in str(file_path):
                rel_path = file_path.relative_to(controllers_dir)
                routers.append(str(rel_path))
        
        return sorted(routers)
    
    def extract_all_endpoints(self) -> List[APIEndpoint]:
        """Extract all API endpoints from routers."""
        controllers_dir = self.src_root / "presentation" / "http" / "controllers"
        endpoints = []
        
        # Pattern to match FastAPI route decorators
        route_pattern = re.compile(
            r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']+)["\']'
        )
        
        for file_path in controllers_dir.rglob("*.py"):
            if "__pycache__" not in str(file_path):
                try:
                    content = file_path.read_text()
                    for line_num, line in enumerate(content.split('\n'), 1):
                        match = route_pattern.search(line)
                        if match:
                            method = match.group(1).upper()
                            path = match.group(2)
                            
                            endpoints.append(APIEndpoint(
                                method=method,
                                path=path,
                                file_path=str(file_path.relative_to(self.backend_root)),
                                line_number=line_num
                            ))
                except Exception as e:
                    print(f"   ⚠️  Error reading {file_path}: {e}")
        
        return endpoints
    
    def map_features(self, entities: List[str], app_modules: List[str], 
                    routers: List[str], endpoints: List[APIEndpoint]):
        """Map backend components to features."""
        
        # Feature mapping based on application modules
        for module in app_modules:
            if module not in self.features:
                self.features[module] = BackendFeature(name=module)
            
            self.features[module].application_modules.append(module)
            
            # Find related entities
            for entity in entities:
                if module in entity.lower() or self._is_related(module, entity):
                    self.features[module].domain_entities.append(entity)
            
            # Find related routers
            for router in routers:
                if module in router.lower():
                    self.features[module].routers.append(router)
            
            # Find related endpoints
            for endpoint in endpoints:
                if f"/{module}/" in endpoint.path or module in endpoint.file_path:
                    self.features[module].api_endpoints.append(endpoint)
    
    def _is_related(self, module: str, entity: str) -> bool:
        """Check if entity is related to module."""
        # Simple heuristic - can be enhanced
        module_keywords = {
            'chat': ['conversation', 'message', 'agent'],
            'portfolio': ['portfolio', 'position', 'exposure'],
            'alerts': ['alert', 'notification'],
            'graph': ['protocol', 'relationship'],
            'ml': ['prediction', 'model'],
            'projects': ['project', 'knowledge', 'assignment'],
            'subscription': ['subscription', 'payment'],
            'auth': ['user', 'session', 'auth'],
        }
        
        keywords = module_keywords.get(module, [module])
        return any(kw in entity.lower() for kw in keywords)
    
    def generate_report(self) -> str:
        """Generate comprehensive analysis report."""
        lines = []
        lines.append("=" * 100)
        lines.append("COMPREHENSIVE BACKEND IMPLEMENTATION ANALYSIS")
        lines.append("=" * 100)
        lines.append("")
        
        # Summary stats
        total_endpoints = sum(len(f.api_endpoints) for f in self.features.values())
        total_entities = len(set(e for f in self.features.values() for e in f.domain_entities))
        
        lines.append("📊 SUMMARY STATISTICS:")
        lines.append(f"   • Total Features: {len(self.features)}")
        lines.append(f"   • Total API Endpoints: {total_endpoints}")
        lines.append(f"   • Total Domain Entities: {total_entities}")
        lines.append(f"   • Total Routers: {sum(len(f.routers) for f in self.features.values())}")
        lines.append("")
        
        # Feature breakdown
        lines.append("=" * 100)
        lines.append("FEATURE BREAKDOWN")
        lines.append("=" * 100)
        lines.append("")
        
        for feature_name in sorted(self.features.keys()):
            feature = self.features[feature_name]
            lines.append(f"\n📦 FEATURE: {feature_name.upper()}")
            lines.append("-" * 100)
            
            if feature.domain_entities:
                lines.append(f"\n   Domain Entities ({len(feature.domain_entities)}):")
                for entity in sorted(feature.domain_entities):
                    lines.append(f"      • {entity}")
            
            if feature.routers:
                lines.append(f"\n   Routers ({len(feature.routers)}):")
                for router in sorted(feature.routers):
                    lines.append(f"      • {router}")
            
            if feature.api_endpoints:
                lines.append(f"\n   API Endpoints ({len(feature.api_endpoints)}):")
                # Group by method
                by_method = {}
                for ep in feature.api_endpoints:
                    if ep.method not in by_method:
                        by_method[ep.method] = []
                    by_method[ep.method].append(ep)
                
                for method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']:
                    if method in by_method:
                        for ep in sorted(by_method[method], key=lambda x: x.path):
                            lines.append(f"      • {ep.method:6} {ep.path}")
            
            lines.append("")
        
        return "\n".join(lines)


def main():
    """Main entry point."""
    backend_root = Path(__file__).parent.parent
    
    analyzer = BackendAnalyzer(backend_root)
    report = analyzer.analyze()
    
    # Save report
    output_file = backend_root / "docs" / "BACKEND_IMPLEMENTATION_ANALYSIS.md"
    output_file.write_text(report)
    
    print("=" * 100)
    print(f"✅ Analysis Complete!")
    print(f"📄 Report saved to: {output_file}")
    print("=" * 100)
    
    # Print summary
    print(report)


if __name__ == "__main__":
    main()
