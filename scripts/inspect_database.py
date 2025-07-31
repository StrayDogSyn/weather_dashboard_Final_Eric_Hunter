#!/usr/bin/env python3
"""
Database Inspector for Weather Dashboard

Inspects the SQLite database and provides detailed information about:
- Database file status and metadata
- Table structure and record counts
- Sample data from key tables
- Data export capabilities
- Query execution interface

Usage:
    python inspect_database.py [options]
    python inspect_database.py --export json
    python inspect_database.py --query "SELECT * FROM weather_history LIMIT 5"
"""

import os
import sqlite3
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import common utilities
from common.base_script import BaseScript
from common.cli_utils import CLIUtils
from common.file_utils import FileUtils


class DatabaseInspector(BaseScript):
    """Database inspection and analysis tool."""
    
    def __init__(self):
        super().__init__(
            name="inspect_database",
            description="Inspect Weather Dashboard SQLite database",
            version="2.0.0"
        )
        
        # Get configuration
        self.db_config = self.config.get('scripts.inspect_database', {})
        self.db_file = self.db_config.get('database_file', 'weather_dashboard.db')
        self.sample_size = self.db_config.get('sample_size', 5)
        self.tables_to_inspect = self.db_config.get('tables_to_inspect', [
            'weather_history', 'user_preferences', 'favorite_cities'
        ])
        self.export_formats = self.db_config.get('export_formats', ['json', 'csv', 'yaml'])
        
        # Find database file
        self.db_path = self._find_database_file()
    
    def setup_cli(self) -> CLIUtils:
        """Setup command line interface."""
        cli = CLIUtils(
            script_name=self.name,
            description=self.description,
            version=self.version
        )
        
        # Add arguments
        cli.add_argument(
            '--database', '-d',
            type=str,
            help=f'Database file path (default: {self.db_file})'
        )
        
        cli.add_argument(
            '--export', '-e',
            choices=self.export_formats,
            help='Export data to specified format'
        )
        
        cli.add_argument(
            '--output', '-o',
            type=str,
            help='Output file for export (default: auto-generated)'
        )
        
        cli.add_argument(
            '--query', '-q',
            type=str,
            help='Execute custom SQL query'
        )
        
        cli.add_argument(
            '--table', '-t',
            type=str,
            help='Focus on specific table'
        )
        
        cli.add_argument(
            '--sample-size', '-s',
            type=int,
            default=self.sample_size,
            help=f'Number of sample records to show (default: {self.sample_size})'
        )
        
        cli.add_argument(
            '--stats-only',
            action='store_true',
            help='Show only statistics, no sample data'
        )
        
        cli.add_common_arguments()
        
        return cli
    
    def _find_database_file(self) -> Optional[Path]:
        """Find the database file in common locations."""
        possible_paths = [
            Path(self.db_file),
            Path('data') / self.db_file,
            Path('..') / 'data' / self.db_file,
            Path('../..') / 'data' / self.db_file,
            self.project_root / 'data' / self.db_file,
            self.project_root / self.db_file
        ]
        
        for path in possible_paths:
            if path.exists():
                return path.resolve()
        
        return None
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database file information."""
        if not self.db_path or not self.db_path.exists():
            return {
                'exists': False,
                'path': str(self.db_path) if self.db_path else 'Not found',
                'error': 'Database file not found'
            }
        
        try:
            stat = self.db_path.stat()
            return {
                'exists': True,
                'path': str(self.db_path),
                'size_bytes': stat.st_size,
                'size_human': FileUtils.format_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'readable': os.access(self.db_path, os.R_OK),
                'writable': os.access(self.db_path, os.W_OK)
            }
        except Exception as e:
            return {
                'exists': True,
                'path': str(self.db_path),
                'error': f'Error accessing file: {e}'
            }
    
    def get_table_info(self, connection: sqlite3.Connection) -> List[Dict[str, Any]]:
        """Get information about all tables in the database."""
        cursor = connection.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        table_names = [row[0] for row in cursor.fetchall()]
        
        tables_info = []
        for table_name in table_names:
            try:
                # Get record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                record_count = cursor.fetchone()[0]
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # Get table size estimate
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                sample_row = cursor.fetchone()
                estimated_size = len(str(sample_row)) * record_count if sample_row else 0
                
                tables_info.append({
                    'name': table_name,
                    'record_count': record_count,
                    'column_count': len(columns),
                    'columns': [{
                        'name': col[1],
                        'type': col[2],
                        'not_null': bool(col[3]),
                        'primary_key': bool(col[5])
                    } for col in columns],
                    'estimated_size_bytes': estimated_size,
                    'estimated_size_human': FileUtils.format_size(estimated_size)
                })
            
            except Exception as e:
                tables_info.append({
                    'name': table_name,
                    'error': f'Error inspecting table: {e}'
                })
        
        return tables_info
    
    def get_sample_data(self, connection: sqlite3.Connection, table_name: str, limit: int = None) -> Dict[str, Any]:
        """Get sample data from a specific table."""
        if limit is None:
            limit = self.sample_size
        
        cursor = connection.cursor()
        
        try:
            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT {limit}")
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            sample_data = []
            for row in rows:
                sample_data.append(dict(zip(columns, row)))
            
            return {
                'table_name': table_name,
                'columns': columns,
                'sample_data': sample_data,
                'sample_count': len(sample_data)
            }
        
        except Exception as e:
            return {
                'table_name': table_name,
                'error': f'Error getting sample data: {e}'
            }
    
    def execute_query(self, connection: sqlite3.Connection, query: str) -> Dict[str, Any]:
        """Execute custom SQL query."""
        cursor = connection.cursor()
        
        try:
            cursor.execute(query)
            
            # Check if it's a SELECT query
            if query.strip().upper().startswith('SELECT'):
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                
                # Convert to list of dictionaries
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                
                return {
                    'query': query,
                    'columns': columns,
                    'results': results,
                    'row_count': len(results)
                }
            else:
                # For non-SELECT queries
                connection.commit()
                return {
                    'query': query,
                    'rows_affected': cursor.rowcount,
                    'message': 'Query executed successfully'
                }
        
        except Exception as e:
            return {
                'query': query,
                'error': f'Error executing query: {e}'
            }
    
    def export_data(self, data: Dict[str, Any], format_type: str, output_file: str = None) -> str:
        """Export data to specified format."""
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'database_export_{timestamp}.{format_type}'
        
        output_path = Path(output_file)
        
        try:
            if format_type == 'json':
                # Convert datetime objects to strings for JSON serialization
                json_data = self._prepare_for_json(data)
                FileUtils.write_json_file(output_path, json_data, indent=2)
            
            elif format_type == 'yaml':
                # Convert datetime objects to strings for YAML serialization
                yaml_data = self._prepare_for_json(data)
                FileUtils.write_yaml_file(output_path, yaml_data)
            
            elif format_type == 'csv':
                self._export_to_csv(data, output_path)
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            return str(output_path)
        
        except Exception as e:
            self.logger.error(f"Error exporting data: {e}")
            raise
    
    def _prepare_for_json(self, data: Any) -> Any:
        """Prepare data for JSON/YAML serialization by converting datetime objects."""
        if isinstance(data, datetime):
            return data.isoformat()
        elif isinstance(data, dict):
            return {key: self._prepare_for_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_json(item) for item in data]
        else:
            return data
    
    def _export_to_csv(self, data: Dict[str, Any], output_path: Path) -> None:
        """Export data to CSV format."""
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            if 'tables' in data:
                # Export all tables
                writer = csv.writer(csvfile)
                
                for table_info in data['tables']:
                    if 'error' in table_info:
                        continue
                    
                    # Write table header
                    writer.writerow([f"Table: {table_info['name']}"])
                    writer.writerow([f"Records: {table_info['record_count']}"])
                    writer.writerow([])
                    
                    # Write column headers
                    if 'columns' in table_info:
                        headers = [col['name'] for col in table_info['columns']]
                        writer.writerow(headers)
                    
                    writer.writerow([])
            
            elif 'results' in data:
                # Export query results
                writer = csv.writer(csvfile)
                
                if data['columns']:
                    writer.writerow(data['columns'])
                
                for result in data['results']:
                    writer.writerow([result.get(col, '') for col in data['columns']])
    
    def run_inspection(self, args) -> Dict[str, Any]:
        """Run the database inspection."""
        # Override database path if provided
        if args.database:
            self.db_path = Path(args.database)
        
        # Get basic database info
        db_info = self.get_database_info()
        
        if not db_info['exists'] or 'error' in db_info:
            return {
                'database_info': db_info,
                'success': False
            }
        
        try:
            # Connect to database
            connection = sqlite3.connect(self.db_path)
            
            # Get table information
            tables_info = self.get_table_info(connection)
            
            # Get sample data if requested
            sample_data = {}
            if not args.stats_only:
                tables_to_sample = [args.table] if args.table else self.tables_to_inspect
                
                for table_name in tables_to_sample:
                    # Check if table exists
                    table_exists = any(t['name'] == table_name for t in tables_info)
                    if table_exists:
                        sample_data[table_name] = self.get_sample_data(
                            connection, table_name, args.sample_size
                        )
            
            # Execute custom query if provided
            query_result = None
            if args.query:
                query_result = self.execute_query(connection, args.query)
            
            connection.close()
            
            return {
                'database_info': db_info,
                'tables': tables_info,
                'sample_data': sample_data,
                'query_result': query_result,
                'success': True
            }
        
        except Exception as e:
            self.logger.error(f"Error inspecting database: {e}")
            return {
                'database_info': db_info,
                'error': str(e),
                'success': False
            }
    
    def display_results(self, results: Dict[str, Any], args) -> None:
        """Display inspection results."""
        cli = CLIUtils(self.name, self.description, self.version)
        
        # Display header
        cli.print_header("Database Inspector", "Weather Dashboard SQLite Analysis")
        
        # Database info
        db_info = results['database_info']
        cli.print_section("Database Information")
        
        if not db_info['exists']:
            cli.print_status(f"Database file not found: {db_info['path']}", "error")
            return
        
        if 'error' in db_info:
            cli.print_status(db_info['error'], "error")
            return
        
        print(f"📁 Path: {db_info['path']}")
        print(f"📊 Size: {db_info['size_human']} ({db_info['size_bytes']:,} bytes)")
        print(f"📅 Modified: {db_info['modified']}")
        print(f"🔒 Permissions: {'Read' if db_info['readable'] else 'No Read'}, {'Write' if db_info['writable'] else 'No Write'}")
        
        if not results['success']:
            if 'error' in results:
                cli.print_status(results['error'], "error")
            return
        
        # Tables information
        if 'tables' in results:
            cli.print_section("Tables Overview")
            
            table_data = []
            for table in results['tables']:
                if 'error' in table:
                    table_data.append([table['name'], 'ERROR', table['error'], ''])
                else:
                    table_data.append([
                        table['name'],
                        f"{table['record_count']:,}",
                        str(table['column_count']),
                        table['estimated_size_human']
                    ])
            
            print(cli.format_table(
                ['Table Name', 'Records', 'Columns', 'Est. Size'],
                table_data
            ))
        
        # Sample data
        if 'sample_data' in results and results['sample_data'] and not args.stats_only:
            for table_name, sample_info in results['sample_data'].items():
                if 'error' in sample_info:
                    cli.print_status(f"Error getting sample data from {table_name}: {sample_info['error']}", "error")
                    continue
                
                cli.print_section(f"Sample Data: {table_name}")
                
                if sample_info['sample_data']:
                    # Display as formatted table
                    headers = sample_info['columns']
                    rows = []
                    
                    for record in sample_info['sample_data']:
                        row = [str(record.get(col, '')) for col in headers]
                        rows.append(row)
                    
                    print(cli.format_table(headers, rows))
                else:
                    print("No data found in table.")
        
        # Query results
        if 'query_result' in results and results['query_result']:
            query_result = results['query_result']
            cli.print_section("Query Results")
            
            if 'error' in query_result:
                cli.print_status(f"Query error: {query_result['error']}", "error")
            elif 'results' in query_result:
                print(f"Query: {query_result['query']}")
                print(f"Rows returned: {query_result['row_count']}")
                
                if query_result['results']:
                    headers = query_result['columns']
                    rows = []
                    
                    for record in query_result['results']:
                        row = [str(record.get(col, '')) for col in headers]
                        rows.append(row)
                    
                    print(cli.format_table(headers, rows))
            else:
                print(f"Query: {query_result['query']}")
                print(f"Rows affected: {query_result['rows_affected']}")
                print(query_result['message'])
        
        # Summary
        if 'tables' in results:
            total_records = sum(t.get('record_count', 0) for t in results['tables'] if 'record_count' in t)
            total_tables = len(results['tables'])
            
            cli.print_summary("Summary", {
                'Total Tables': total_tables,
                'Total Records': f"{total_records:,}",
                'Database Size': db_info['size_human'],
                'Last Modified': db_info['modified'].strftime('%Y-%m-%d %H:%M:%S')
            })
    
    def run(self) -> int:
        """Main execution method."""
        try:
            # Setup CLI and parse arguments
            cli = self.setup_cli()
            args = cli.parse_args()
            
            # Configure logging based on arguments
            self.configure_logging(args)
            
            self.logger.info(f"Starting database inspection: {self.db_path}")
            
            # Run inspection
            results = self.run_inspection(args)
            
            # Display results
            if not args.quiet:
                self.display_results(results, args)
            
            # Export if requested
            if args.export and results['success']:
                try:
                    output_file = self.export_data(results, args.export, args.output)
                    cli.print_status(f"Data exported to: {output_file}", "success")
                except Exception as e:
                    cli.print_status(f"Export failed: {e}", "error")
                    return 1
            
            if results['success']:
                cli.print_status("Database inspection completed successfully!", "success")
                return 0
            else:
                cli.print_status("Database inspection failed", "error")
                return 1
        
        except KeyboardInterrupt:
            self.logger.info("Database inspection cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point."""
    inspector = DatabaseInspector()
    return inspector.run()


if __name__ == "__main__":
    exit(main())
