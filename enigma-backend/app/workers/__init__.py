"""
ENIGMA Workers package.

Each Worker is independently executable (Engineering Principle 3).  Workers are
auto-discovered and registered with the ExecutionEngine at startup via
``app.engine.registry.register_all()``.
"""
