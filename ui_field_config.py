#!/usr/bin/env python3
"""
Bidirectional UI Field Configuration System
Automatically syncs database fields with UI columns
"""

import sqlite3
import json
from typing import Dict, List, Tuple

# Master field configuration - single source of truth
UI_FIELDS = [
    {
        'id': 'name',
        'header': 'Token',
        'db_field': 'name',
        'sortable': True,
        'type': 'text',
        'display_format': 'token_name',
        'width': 'auto'
    },
    {
        'id': 'price',
        'header': 'Price',
        'db_field': 'price_usd',
        'sortable': True,
        'type': 'currency',
        'display_format': 'price',
        'width': '100px'
    },
    {
        'id': 'change_5m',
        'header': '5m',
        'db_field': 'price_change_5m',
        'sortable': True,
        'type': 'percentage',
        'display_format': 'price_change',
        'width': '80px'
    },
    {
        'id': 'change_1h',
        'header': '1h',
        'db_field': 'price_change_1h',
        'sortable': True,
        'type': 'percentage',
        'display_format': 'price_change',
        'width': '80px'
    },
    {
        'id': 'change_24h',
        'header': '24h',
        'db_field': 'price_change_24h',
        'sortable': True,
        'type': 'percentage',
        'display_format': 'price_change',
        'width': '80px'
    },
    {
        'id': 'market_cap',
        'header': 'Market Cap',
        'db_field': 'market_cap',
        'sortable': True,
        'type': 'currency',
        'display_format': 'number',
        'width': '120px'
    },
    {
        'id': 'liquidity',
        'header': 'Liquidity',
        'db_field': 'liquidity',
        'sortable': True,
        'type': 'currency',
        'display_format': 'number',
        'width': '120px'
    },
    {
        'id': 'volume24h',
        'header': 'Volume 24h',
        'db_field': 'volume24h',
        'sortable': True,
        'type': 'currency',
        'display_format': 'number',
        'width': '120px'
    },
    {
        'id': 'holders',
        'header': 'Holders',
        'db_field': 'current_holder_count',
        'sortable': True,
        'type': 'number',
        'display_format': 'number',
        'width': '100px'
    },
    {
        'id': 'holder_growth',
        'header': 'Growth 24h',
        'db_field': 'holder_growth_24h',
        'sortable': True,
        'type': 'percentage',
        'display_format': 'price_change',
        'width': '100px'
    },
    {
        'id': 'risk',
        'header': 'Risk',
        'db_field': 'risk_score',
        'sortable': True,
        'type': 'number',
        'display_format': 'risk',
        'width': '80px'
    },
    {
        'id': 'platform',
        'header': 'Platform',
        'db_field': 'is_pump_token',
        'sortable': True,
        'type': 'boolean',
        'display_format': 'platform',
        'width': '100px'
    },
    {
        'id': 'score',
        'header': 'Score',
        'db_field': 'composite_score',
        'sortable': True,
        'type': 'number',
        'display_format': 'score',
        'width': '80px'
    },
    {
        'id': 'links',
        'header': 'Links',
        'db_field': None,  # Computed field
        'sortable': False,
        'type': 'links',
        'display_format': 'links',
        'width': '150px'
    }
]

class UIFieldManager:
    def __init__(self, database_file='raydium_pools.db'):
        self.database_file = database_file
        self.fields = UI_FIELDS.copy()

    def add_field(self, field_config: Dict, position: int = None):
        """Add a new field to both database and UI"""
        if position is None:
            position = len(self.fields) - 1  # Before links column

        # Add to database if needed
        if field_config.get('db_field'):
            self._add_db_field(field_config)

        # Add to UI configuration
        self.fields.insert(position, field_config)

        # Regenerate UI components
        self._update_ui_components()

        print(f"✅ Added field '{field_config['id']}' at position {position}")

    def remove_field(self, field_id: str):
        """Remove field from both database and UI"""
        field = self.get_field_by_id(field_id)
        if not field:
            print(f"❌ Field '{field_id}' not found")
            return

        # Remove from UI
        self.fields = [f for f in self.fields if f['id'] != field_id]

        # Note: We don't drop DB columns for safety
        print(f"✅ Removed field '{field_id}' from UI")

        # Regenerate UI components
        self._update_ui_components()

    def get_field_by_id(self, field_id: str) -> Dict:
        """Get field configuration by ID"""
        return next((f for f in self.fields if f['id'] == field_id), None)

    def get_sortable_fields(self) -> List[Dict]:
        """Get all sortable fields"""
        return [f for f in self.fields if f['sortable']]

    def get_db_fields(self) -> List[str]:
        """Get list of database fields to query"""
        return [f['db_field'] for f in self.fields if f['db_field']]

    def _add_db_field(self, field_config: Dict):
        """Add field to database"""
        if not field_config.get('db_field'):
            return

        db_field = field_config['db_field']
        field_type = self._get_sql_type(field_config['type'])

        conn = sqlite3.connect(self.database_file)
        try:
            # Check if field exists
            cursor = conn.execute("PRAGMA table_info(pools)")
            existing_fields = [row[1] for row in cursor.fetchall()]

            if db_field not in existing_fields:
                conn.execute(f'ALTER TABLE pools ADD COLUMN {db_field} {field_type}')
                print(f"✅ Added database field: {db_field} {field_type}")
            else:
                print(f"📋 Database field already exists: {db_field}")

            conn.commit()
        except Exception as e:
            print(f"❌ Database error: {e}")
        finally:
            conn.close()

    def _get_sql_type(self, field_type: str) -> str:
        """Convert field type to SQL type"""
        type_map = {
            'text': 'TEXT',
            'number': 'INTEGER',
            'currency': 'REAL',
            'percentage': 'REAL',
            'boolean': 'INTEGER'
        }
        return type_map.get(field_type, 'TEXT')

    def _update_ui_components(self):
        """Generate updated UI components"""
        self.generate_table_headers()
        self.generate_table_cells()
        self.generate_sort_function()
        self.generate_filter_fields()

    def generate_table_headers(self) -> str:
        """Generate HTML table headers"""
        headers = []
        for i, field in enumerate(self.fields):
            if field['sortable']:
                headers.append(f'''<th onclick="sortTable({i})" class="sortable ${{currentSort.column === {i} ? 'sort-' + currentSort.direction : ''}}">{field['header']}</th>''')
            else:
                headers.append(f'''<th>{field['header']}</th>''')

        return '\n                            '.join(headers)

    def generate_table_cells(self) -> str:
        """Generate JavaScript table cell templates"""
        cells = []
        for field in self.fields:
            cell_template = self._get_cell_template(field)
            cells.append(cell_template)

        return '\n                                    '.join(cells)

    def _get_cell_template(self, field: Dict) -> str:
        """Get cell template for field type"""
        templates = {
            'token_name': '''<td class="token-name-cell">
                                        <div>${token.name || 'Unknown Token'}</div>
                                        <div class="token-address" onclick="copyAddress('${token.token_address}')" title="Click to copy: ${token.token_address}">
                                            ${token.token_address?.substring(0, 4)}...${token.token_address?.substring(-4)}
                                            <span class="copy-icon">📋</span>
                                        </div>
                                    </td>''',
            'price': '''<td class="number-cell" data-value="${token.price_usd || 0}">$${token.price_usd?.toFixed(6) || 'N/A'}</td>''',
            'price_change': f'''<td class="price-change-cell" data-value="${{token.{field['db_field']} || 0}}">
                                        <span class="price-change ${{getPriceChangeClass(token.{field['db_field']})}}">
                                            ${{token.{field['db_field']} ? (token.{field['db_field']} > 0 ? '+' : '') + token.{field['db_field']}.toFixed(2) + '%' : 'N/A'}}
                                        </span>
                                    </td>''',
            'number': f'''<td class="number-cell" data-value="${{token.{field['db_field']} || 0}}">${{token.{field['db_field']}?.toLocaleString() || 'N/A'}}</td>''',
            'risk': '''<td class="risk-cell" data-value="${token.risk_score || 0}">
                                        <span class="risk-badge ${getRiskClass(token.risk_score)}">
                                            ${getRiskLabel(token.risk_score)} (${token.risk_score}/10)
                                        </span>
                                    </td>''',
            'platform': '''<td class="platform-cell">
                                        ${token.is_pump_token ?
                                            '<span class="pump-badge">Pump.fun</span>' :
                                            '<span class="regular-badge">Other</span>'
                                        }
                                    </td>''',
            'score': '''<td class="score-cell" data-value="${token.composite_score || 0}">
                                        <span class="composite-score ${scoreClass}">
                                            ${token.composite_score > 0 ? '+' : ''}${token.composite_score}
                                        </span>
                                    </td>''',
            'links': '''<td class="links-cell">
                                        <a href="${token.solscan_url}" target="_blank" rel="noopener noreferrer">Solscan</a>
                                        <a href="${token.dexscreener_url}" target="_blank" rel="noopener noreferrer">DexScreener</a>
                                    </td>'''
        }

        return templates.get(field['display_format'], f'''<td class="text-cell">${{token.{field['db_field']} || 'N/A'}}</td>''')

    def generate_sort_function(self) -> str:
        """Generate JavaScript sort function cases"""
        cases = []
        for i, field in enumerate(self.fields):
            if not field['sortable']:
                continue

            if field['type'] == 'text':
                cases.append(f'''case {i}: // {field['header']}
                        aVal = (a.{field['db_field']} || '').toLowerCase();
                        bVal = (b.{field['db_field']} || '').toLowerCase();
                        break;''')
            elif field['type'] == 'boolean':
                cases.append(f'''case {i}: // {field['header']}
                        aVal = a.{field['db_field']} ? 1 : 0;
                        bVal = b.{field['db_field']} ? 1 : 0;
                        break;''')
            else:
                cases.append(f'''case {i}: // {field['header']}
                        aVal = a.{field['db_field']} || 0;
                        bVal = b.{field['db_field']} || 0;
                        break;''')

        return '\n                    '.join(cases)

# Example usage
def demo_add_field():
    """Demo: Add a new field"""
    manager = UIFieldManager()

    # Add a new field: Trading Volume 1h
    new_field = {
        'id': 'volume_1h',
        'header': 'Volume 1h',
        'db_field': 'volume_1h',
        'sortable': True,
        'type': 'currency',
        'display_format': 'number',
        'width': '120px'
    }

    manager.add_field(new_field, position=8)  # After Volume 24h

    print("\n📋 Updated field configuration:")
    for i, field in enumerate(manager.fields):
        print(f"{i:2d}. {field['header']:15} -> {field['db_field']}")

if __name__ == "__main__":
    demo_add_field()