#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Odoo CRM API Interaction Demo Script

This script demonstrates comprehensive interaction with Odoo CRM API using both XML-RPC and JSON-RPC methods.
It includes authentication, CRUD operations, search and filter functionality, batch operations, and error handling.

Compatible with Python 3.x and Odoo's API specifications.
"""

import xmlrpc.client
import requests
import json
import logging
import time
import sys
from typing import Dict, List, Any, Union, Optional, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("odoo_api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("odoo_api")

class OdooAPI:
    """
    A class to interact with Odoo CRM API using both XML-RPC and JSON-RPC methods.
    
    Attributes:
        url (str): Base URL of the Odoo instance
        db (str): Database name
        username (str): Username for authentication
        password (str): Password for authentication
        uid (int): User ID after successful authentication
        xmlrpc_common (xmlrpc.client.ServerProxy): XML-RPC common endpoint
        xmlrpc_models (xmlrpc.client.ServerProxy): XML-RPC models endpoint
        jsonrpc_url (str): JSON-RPC URL endpoint
        session_id (str): Session ID for JSON-RPC authentication
    """
    
    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize the OdooAPI class with connection parameters.
        
        Args:
            url (str): Base URL of the Odoo instance
            db (str): Database name
            username (str): Username for authentication
            password (str): Password for authentication
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.xmlrpc_common = None
        self.xmlrpc_models = None
        self.jsonrpc_url = f"{self.url}/jsonrpc"
        self.session_id = None
        
        # Initialize logger
        self.logger = logger
        
    def xmlrpc_authenticate(self) -> bool:
        """
        Authenticate using XML-RPC protocol.
        
        Returns:
            bool: True if authentication is successful, False otherwise
        """
        try:
            self.logger.info("Authenticating via XML-RPC...")
            self.xmlrpc_common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
            self.uid = self.xmlrpc_common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                self.xmlrpc_models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
                self.logger.info(f"XML-RPC Authentication successful. UID: {self.uid}")
                return True
            else:
                self.logger.error("XML-RPC Authentication failed")
                return False
                
        except Exception as e:
            self.logger.error(f"XML-RPC Authentication error: {str(e)}")
            return False
    
    def jsonrpc_authenticate(self) -> bool:
        """
        Authenticate using JSON-RPC protocol.
        
        Returns:
            bool: True if authentication is successful, False otherwise
        """
        try:
            self.logger.info("Authenticating via JSON-RPC...")
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "common",
                    "method": "login",
                    "args": [self.db, self.username, self.password]
                },
                "id": 1
            }
            
            response = requests.post(
                self.jsonrpc_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result and result['result']:
                    self.uid = result['result']
                    self.session_id = response.cookies.get('session_id')
                    self.logger.info(f"JSON-RPC Authentication successful. UID: {self.uid}")
                    return True
                else:
                    self.logger.error("JSON-RPC Authentication failed")
                    return False
            else:
                self.logger.error(f"JSON-RPC Authentication failed with status code: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"JSON-RPC Authentication error: {str(e)}")
            return False
    
    def xmlrpc_execute(self, model: str, method: str, *args) -> Any:
        """
        Execute a method on a model using XML-RPC.
        
        Args:
            model (str): The model name
            method (str): The method to execute
            *args: Additional arguments for the method
            
        Returns:
            Any: Result of the method execution
        """
        try:
            if not self.uid or not self.xmlrpc_models:
                if not self.xmlrpc_authenticate():
                    return None
                    
            result = self.xmlrpc_models.execute_kw(
                self.db, self.uid, self.password, model, method, args
            )
            return result
            
        except Exception as e:
            self.logger.error(f"XML-RPC execution error: {str(e)}")
            return None
    
    def jsonrpc_execute(self, model: str, method: str, *args) -> Any:
        """
        Execute a method on a model using JSON-RPC.
        
        Args:
            model (str): The model name
            method (str): The method to execute
            *args: Additional arguments for the method
            
        Returns:
            Any: Result of the method execution
        """
        try:
            if not self.uid:
                if not self.jsonrpc_authenticate():
                    return None
                    
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "service": "object",
                    "method": "execute_kw",
                    "args": [self.db, self.uid, self.password, model, method, args]
                },
                "id": int(time.time())
            }
            
            cookies = {}
            if self.session_id:
                cookies['session_id'] = self.session_id
                
            response = requests.post(
                self.jsonrpc_url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                cookies=cookies
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'result' in result:
                    return result['result']
                elif 'error' in result:
                    self.logger.error(f"JSON-RPC execution error: {result['error']}")
                    return None
            else:
                self.logger.error(f"JSON-RPC execution failed with status code: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"JSON-RPC execution error: {str(e)}")
            return None
    
    # CRUD Operations for CRM Leads
    
    def create_lead_xmlrpc(self, lead_data: Dict[str, Any]) -> int:
        """
        Create a new lead using XML-RPC.
        
        Args:
            lead_data (Dict[str, Any]): Lead data dictionary
            
        Returns:
            int: ID of the created lead or None if failed
        """
        try:
            self.logger.info("Creating lead via XML-RPC...")
            lead_id = self.xmlrpc_execute('crm.lead', 'create', [lead_data])
            if lead_id:
                self.logger.info(f"Lead created successfully with ID: {lead_id}")
            return lead_id
        except Exception as e:
            self.logger.error(f"Error creating lead via XML-RPC: {str(e)}")
            return None
    
    def create_lead_jsonrpc(self, lead_data: Dict[str, Any]) -> int:
        """
        Create a new lead using JSON-RPC.
        
        Args:
            lead_data (Dict[str, Any]): Lead data dictionary
            
        Returns:
            int: ID of the created lead or None if failed
        """
        try:
            self.logger.info("Creating lead via JSON-RPC...")
            lead_id = self.jsonrpc_execute('crm.lead', 'create', [lead_data])
            if lead_id:
                self.logger.info(f"Lead created successfully with ID: {lead_id}")
            return lead_id
        except Exception as e:
            self.logger.error(f"Error creating lead via JSON-RPC: {str(e)}")
            return None
    
    def read_lead_xmlrpc(self, lead_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Read a lead using XML-RPC.
        
        Args:
            lead_id (int): ID of the lead to read
            fields (List[str], optional): List of fields to read. Defaults to None (all fields).
            
        Returns:
            Dict[str, Any]: Lead data or None if failed
        """
        try:
            self.logger.info(f"Reading lead {lead_id} via XML-RPC...")
            if fields is None:
                fields = []
            lead_data = self.xmlrpc_execute('crm.lead', 'read', [lead_id], {'fields': fields})
            if lead_data and len(lead_data) > 0:
                self.logger.info(f"Lead {lead_id} read successfully")
                return lead_data[0]
            else:
                self.logger.warning(f"Lead {lead_id} not found")
                return None
        except Exception as e:
            self.logger.error(f"Error reading lead {lead_id} via XML-RPC: {str(e)}")
            return None
    
    def read_lead_jsonrpc(self, lead_id: int, fields: List[str] = None) -> Dict[str, Any]:
        """
        Read a lead using JSON-RPC.
        
        Args:
            lead_id (int): ID of the lead to read
            fields (List[str], optional): List of fields to read. Defaults to None (all fields).
            
        Returns:
            Dict[str, Any]: Lead data or None if failed
        """
        try:
            self.logger.info(f"Reading lead {lead_id} via JSON-RPC...")
            if fields is None:
                fields = []
            lead_data = self.jsonrpc_execute('crm.lead', 'read', [lead_id], {'fields': fields})
            if lead_data and len(lead_data) > 0:
                self.logger.info(f"Lead {lead_id} read successfully")
                return lead_data[0]
            else:
                self.logger.warning(f"Lead {lead_id} not found")
                return None
        except Exception as e:
            self.logger.error(f"Error reading lead {lead_id} via JSON-RPC: {str(e)}")
            return None
    
    def update_lead_xmlrpc(self, lead_id: int, lead_data: Dict[str, Any]) -> bool:
        """
        Update a lead using XML-RPC.
        
        Args:
            lead_id (int): ID of the lead to update
            lead_data (Dict[str, Any]): Updated lead data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating lead {lead_id} via XML-RPC...")
            result = self.xmlrpc_execute('crm.lead', 'write', [lead_id], lead_data)
            if result:
                self.logger.info(f"Lead {lead_id} updated successfully")
            else:
                self.logger.warning(f"Failed to update lead {lead_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error updating lead {lead_id} via XML-RPC: {str(e)}")
            return False
    
    def update_lead_jsonrpc(self, lead_id: int, lead_data: Dict[str, Any]) -> bool:
        """
        Update a lead using JSON-RPC.
        
        Args:
            lead_id (int): ID of the lead to update
            lead_data (Dict[str, Any]): Updated lead data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating lead {lead_id} via JSON-RPC...")
            result = self.jsonrpc_execute('crm.lead', 'write', [lead_id], lead_data)
            if result:
                self.logger.info(f"Lead {lead_id} updated successfully")
            else:
                self.logger.warning(f"Failed to update lead {lead_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error updating lead {lead_id} via JSON-RPC: {str(e)}")
            return False
    
    def delete_lead_xmlrpc(self, lead_id: int) -> bool:
        """
        Delete a lead using XML-RPC.
        
        Args:
            lead_id (int): ID of the lead to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting lead {lead_id} via XML-RPC...")
            result = self.xmlrpc_execute('crm.lead', 'unlink', [lead_id])
            if result:
                self.logger.info(f"Lead {lead_id} deleted successfully")
            else:
                self.logger.warning(f"Failed to delete lead {lead_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting lead {lead_id} via XML-RPC: {str(e)}")
            return False
    
    def delete_lead_jsonrpc(self, lead_id: int) -> bool:
        """
        Delete a lead using JSON-RPC.
        
        Args:
            lead_id (int): ID of the lead to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.logger.info(f"Deleting lead {lead_id} via JSON-RPC...")
            result = self.jsonrpc_execute('crm.lead', 'unlink', [lead_id])
            if result:
                self.logger.info(f"Lead {lead_id} deleted successfully")
            else:
                self.logger.warning(f"Failed to delete lead {lead_id}")
            return result
        except Exception as e:
            self.logger.error(f"Error deleting lead {lead_id} via JSON-RPC: {str(e)}")
            return False
    
    # Search and Filter Operations
    
    def search_leads_xmlrpc(self, domain: List, offset: int = 0, limit: int = None, order: str = None) -> List[int]:
        """
        Search for leads using XML-RPC.
        
        Args:
            domain (List): Search domain
            offset (int, optional): Result offset. Defaults to 0.
            limit (int, optional): Maximum number of records. Defaults to None.
            order (str, optional): Sort order. Defaults to None.
            
        Returns:
            List[int]: List of lead IDs or empty list if failed
        """
        try:
            self.logger.info(f"Searching leads via XML-RPC with domain: {domain}")
            kwargs = {}
            if offset:
                kwargs['offset'] = offset
            if limit:
                kwargs['limit'] = limit
            if order:
                kwargs['order'] = order
                
            lead_ids = self.xmlrpc_execute('crm.lead', 'search', domain, kwargs)
            self.logger.info(f"Found {len(lead_ids)} leads")
            return lead_ids
        except Exception as e:
            self.logger.error(f"Error searching leads via XML-RPC: {str(e)}")
            return []
    
    def search_leads_jsonrpc(self, domain: List, offset: int = 0, limit: int = None, order: str = None) -> List[int]:
        """
        Search for leads using JSON-RPC.
        
        Args:
            domain (List): Search domain
            offset (int, optional): Result offset. Defaults to 0.
            limit (int, optional): Maximum number of records. Defaults to None.
            order (str, optional): Sort order. Defaults to None.
            
        Returns:
            List[int]: List of lead IDs or empty list if failed
        """
        try:
            self.logger.info(f"Searching leads via JSON-RPC with domain: {domain}")
            kwargs = {}
            if offset:
                kwargs['offset'] = offset
            if limit:
                kwargs['limit'] = limit
            if order:
                kwargs['order'] = order
                
            lead_ids = self.jsonrpc_execute('crm.lead', 'search', domain, kwargs)
            self.logger.info(f"Found {len(lead_ids)} leads")
            return lead_ids
        except Exception as e:
            self.logger.error(f"Error searching leads via JSON-RPC: {str(e)}")
            return []
    
    def search_read_leads_xmlrpc(self, domain: List, fields: List[str] = None, 
                                offset: int = 0, limit: int = None, order: str = None) -> List[Dict[str, Any]]:
        """
        Search and read leads in one operation using XML-RPC.
        
        Args:
            domain (List): Search domain
            fields (List[str], optional): Fields to read. Defaults to None (all fields).
            offset (int, optional): Result offset. Defaults to 0.
            limit (int, optional): Maximum number of records. Defaults to None.
            order (str, optional): Sort order. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of lead data dictionaries or empty list if failed
        """
        try:
            self.logger.info(f"Search-reading leads via XML-RPC with domain: {domain}")
            if fields is None:
                fields = []
                
            kwargs = {
                'fields': fields
            }
            if offset:
                kwargs['offset'] = offset
            if limit:
                kwargs['limit'] = limit
            if order:
                kwargs['order'] = order
                
            leads = self.xmlrpc_execute('crm.lead', 'search_read', domain, kwargs)
            self.logger.info(f"Found and read {len(leads)} leads")
            return leads
        except Exception as e:
            self.logger.error(f"Error search-reading leads via XML-RPC: {str(e)}")
            return []
    
    def search_read_leads_jsonrpc(self, domain: List, fields: List[str] = None, 
                                 offset: int = 0, limit: int = None, order: str = None) -> List[Dict[str, Any]]:
        """
        Search and read leads in one operation using JSON-RPC.
        
        Args:
            domain (List): Search domain
            fields (List[str], optional): Fields to read. Defaults to None (all fields).
            offset (int, optional): Result offset. Defaults to 0.
            limit (int, optional): Maximum number of records. Defaults to None.
            order (str, optional): Sort order. Defaults to None.
            
        Returns:
            List[Dict[str, Any]]: List of lead data dictionaries or empty list if failed
        """
        try:
            self.logger.info(f"Search-reading leads via JSON-RPC with domain: {domain}")
            if fields is None:
                fields = []
                
            kwargs = {
                'fields': fields
            }
            if offset:
                kwargs['offset'] = offset
            if limit:
                kwargs['limit'] = limit
            if order:
                kwargs['order'] = order
                
            leads = self.jsonrpc_execute('crm.lead', 'search_read', domain, kwargs)
            self.logger.info(f"Found and read {len(leads)} leads")
            return leads
        except Exception as e:
            self.logger.error(f"Error search-reading leads via JSON-RPC: {str(e)}")
            return []
    
    # Batch Operations
    
    def create_leads_batch_xmlrpc(self, leads_data: List[Dict[str, Any]]) -> List[int]:
        """
        Create multiple leads in batch using XML-RPC.
        
        Args:
            leads_data (List[Dict[str, Any]]): List of lead data dictionaries
            
        Returns:
            List[int]: List of created lead IDs or empty list if failed
        """
        try:
            self.logger.info(f"Creating {len(leads_data)} leads in batch via XML-RPC...")
            lead_ids = []
            
            for lead_data in leads_data:
                lead_id = self.create_lead_xmlrpc(lead_data)
                if lead_id:
                    lead_ids.append(lead_id)
            
            self.logger.info(f"Successfully created {len(lead_ids)} leads in batch")
            return lead_ids
        except Exception as e:
            self.logger.error(f"Error creating leads in batch via XML-RPC: {str(e)}")
            return []
    
    def create_leads_batch_jsonrpc(self, leads_data: List[Dict[str, Any]]) -> List[int]:
        """
        Create multiple leads in batch using JSON-RPC.
        
        Args:
            leads_data (List[Dict[str, Any]]): List of lead data dictionaries
            
        Returns:
            List[int]: List of created lead IDs or empty list if failed
        """
        try:
            self.logger.info(f"Creating {len(leads_data)} leads in batch via JSON-RPC...")
            lead_ids = []
            
            for lead_data in leads_data:
                lead_id = self.create_lead_jsonrpc(lead_data)
                if lead_id:
                    lead_ids.append(lead_id)
            
            self.logger.info(f"Successfully created {len(lead_ids)} leads in batch")
            return lead_ids
        except Exception as e:
            self.logger.error(f"Error creating leads in batch via JSON-RPC: {str(e)}")
            return []
    
    def update_leads_batch_xmlrpc(self, leads_updates: Dict[int, Dict[str, Any]]) -> Dict[int, bool]:
        """
        Update multiple leads in batch using XML-RPC.
        
        Args:
            leads_updates (Dict[int, Dict[str, Any]]): Dictionary mapping lead IDs to update data
            
        Returns:
            Dict[int, bool]: Dictionary mapping lead IDs to update success status
        """
        try:
            self.logger.info(f"Updating {len(leads_updates)} leads in batch via XML-RPC...")
            results = {}
            
            for lead_id, update_data in leads_updates.items():
                success = self.update_lead_xmlrpc(lead_id, update_data)
                results[lead_id] = success
            
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Successfully updated {success_count} out of {len(leads_updates)} leads in batch")
            return results
        except Exception as e:
            self.logger.error(f"Error updating leads in batch via XML-RPC: {str(e)}")
            return {}
    
    def update_leads_batch_jsonrpc(self, leads_updates: Dict[int, Dict[str, Any]]) -> Dict[int, bool]:
        """
        Update multiple leads in batch using JSON-RPC.
        
        Args:
            leads_updates (Dict[int, Dict[str, Any]]): Dictionary mapping lead IDs to update data
            
        Returns:
            Dict[int, bool]: Dictionary mapping lead IDs to update success status
        """
        try:
            self.logger.info(f"Updating {len(leads_updates)} leads in batch via JSON-RPC...")
            results = {}
            
            for lead_id, update_data in leads_updates.items():
                success = self.update_lead_jsonrpc(lead_id, update_data)
                results[lead_id] = success
            
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Successfully updated {success_count} out of {len(leads_updates)} leads in batch")
            return results
        except Exception as e:
            self.logger.error(f"Error updating leads in batch via JSON-RPC: {str(e)}")
            return {}
    
    def delete_leads_batch_xmlrpc(self, lead_ids: List[int]) -> Dict[int, bool]:
        """
        Delete multiple leads in batch using XML-RPC.
        
        Args:
            lead_ids (List[int]): List of lead IDs to delete
            
        Returns:
            Dict[int, bool]: Dictionary mapping lead IDs to deletion success status
        """
        try:
            self.logger.info(f"Deleting {len(lead_ids)} leads in batch via XML-RPC...")
            results = {}
            
            for lead_id in lead_ids:
                success = self.delete_lead_xmlrpc(lead_id)
                results[lead_id] = success
            
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Successfully deleted {success_count} out of {len(lead_ids)} leads in batch")
            return results
        except Exception as e:
            self.logger.error(f"Error deleting leads in batch via XML-RPC: {str(e)}")
            return {}
    
    def delete_leads_batch_jsonrpc(self, lead_ids: List[int]) -> Dict[int, bool]:
        """
        Delete multiple leads in batch using JSON-RPC.
        
        Args:
            lead_ids (List[int]): List of lead IDs to delete
            
        Returns:
            Dict[int, bool]: Dictionary mapping lead IDs to deletion success status
        """
        try:
            self.logger.info(f"Deleting {len(lead_ids)} leads in batch via JSON-RPC...")
            results = {}
            
            for lead_id in lead_ids:
                success = self.delete_lead_jsonrpc(lead_id)
                results[lead_id] = success
            
            success_count = sum(1 for success in results.values() if success)
            self.logger.info(f"Successfully deleted {success_count} out of {len(lead_ids)} leads in batch")
            return results
        except Exception as e:
            self.logger.error(f"Error deleting leads in batch via JSON-RPC: {str(e)}")
            return {}


def demo_usage():
    """
    Demonstrate usage of the OdooAPI class with examples for each operation.
    """
    # Configuration
    odoo_url = "http://localhost:8069"
    odoo_db = "odoo"
    odoo_username = "admin"
    odoo_password = "admin"
    
    # Initialize API
    api = OdooAPI(odoo_url, odoo_db, odoo_username, odoo_password)
    
    print("\n" + "="*80)
    print("ODOO CRM API DEMONSTRATION")
    print("="*80)
    
    # Authentication Demo
    print("\n1. Authentication")
    print("-"*40)
    
    print("\nXML-RPC Authentication:")
    if api.xmlrpc_authenticate():
        print(f"✓ Success! User ID: {api.uid}")
    else:
        print("✗ Failed to authenticate via XML-RPC")
    
    print("\nJSON-RPC Authentication:")
    if api.jsonrpc_authenticate():
        print(f"✓ Success! User ID: {api.uid}")
    else:
        print("✗ Failed to authenticate via JSON-RPC")
    
    # CRUD Operations Demo
    print("\n2. CRUD Operations")
    print("-"*40)
    
    # Create Lead Demo
    print("\nCreating a lead via XML-RPC:")
    lead_data = {
        'name': f"Test Lead XML-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        'partner_name': 'Test Company',
        'contact_name': 'John Doe',
        'email_from': 'john.doe@example.com',
        'phone': '+1234567890',
        'description': 'This is a test lead created via XML-RPC'
    }
    lead_id_xmlrpc = api.create_lead_xmlrpc(lead_data)
    if lead_id_xmlrpc:
        print(f"✓ Lead created with ID: {lead_id_xmlrpc}")
    else:
        print("✗ Failed to create lead")
    
    print("\nCreating a lead via JSON-RPC:")
    lead_data = {
        'name': f"Test Lead JSON-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        'partner_name': 'Test Company',
        'contact_name': 'Jane Smith',
        'email_from': 'jane.smith@example.com',
        'phone': '+0987654321',
        'description': 'This is a test lead created via JSON-RPC'
    }
    lead_id_jsonrpc = api.create_lead_jsonrpc(lead_data)
    if lead_id_jsonrpc:
        print(f"✓ Lead created with ID: {lead_id_jsonrpc}")
    else:
        print("✗ Failed to create lead")
    
    # Read Lead Demo
    if lead_id_xmlrpc:
        print("\nReading a lead via XML-RPC:")
        lead_data = api.read_lead_xmlrpc(lead_id_xmlrpc, ['name', 'contact_name', 'email_from', 'phone'])
        if lead_data:
            print(f"✓ Lead data: {json.dumps(lead_data, indent=2)}")
        else:
            print("✗ Failed to read lead")
    
    if lead_id_jsonrpc:
        print("\nReading a lead via JSON-RPC:")
        lead_data = api.read_lead_jsonrpc(lead_id_jsonrpc, ['name', 'contact_name', 'email_from', 'phone'])
        if lead_data:
            print(f"✓ Lead data: {json.dumps(lead_data, indent=2)}")
        else:
            print("✗ Failed to read lead")
    
    # Update Lead Demo
    if lead_id_xmlrpc:
        print("\nUpdating a lead via XML-RPC:")
        update_data = {
            'name': f"Updated Test Lead XML-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'description': 'This lead was updated via XML-RPC'
        }
        if api.update_lead_xmlrpc(lead_id_xmlrpc, update_data):
            print("✓ Lead updated successfully")
            # Verify update
            lead_data = api.read_lead_xmlrpc(lead_id_xmlrpc, ['name', 'description'])
            print(f"  Updated data: {json.dumps(lead_data, indent=2)}")
        else:
            print("✗ Failed to update lead")
    
    if lead_id_jsonrpc:
        print("\nUpdating a lead via JSON-RPC:")
        update_data = {
            'name': f"Updated Test Lead JSON-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'description': 'This lead was updated via JSON-RPC'
        }
        if api.update_lead_jsonrpc(lead_id_jsonrpc, update_data):
            print("✓ Lead updated successfully")
            # Verify update
            lead_data = api.read_lead_jsonrpc(lead_id_jsonrpc, ['name', 'description'])
            print(f"  Updated data: {json.dumps(lead_data, indent=2)}")
        else:
            print("✗ Failed to update lead")
    
    # Search and Filter Demo
    print("\n3. Search and Filter Operations")
    print("-"*40)
    
    print("\nSearching leads via XML-RPC:")
    domain = [('name', 'like', 'Test Lead')]
    lead_ids = api.search_leads_xmlrpc(domain, limit=5, order='id desc')
    if lead_ids:
        print(f"✓ Found {len(lead_ids)} leads: {lead_ids}")
    else:
        print("✗ No leads found or search failed")
    
    print("\nSearch-reading leads via JSON-RPC:")
    domain = [('name', 'like', 'Test Lead')]
    fields = ['id', 'name', 'contact_name', 'email_from']
    leads = api.search_read_leads_jsonrpc(domain, fields, limit=5, order='id desc')
    if leads:
        print(f"✓ Found {len(leads)} leads:")
        for lead in leads:
            print(f"  - {lead['id']}: {lead['name']} ({lead.get('contact_name', 'N/A')})")
    else:
        print("✗ No leads found or search failed")
    
    # Batch Operations Demo
    print("\n4. Batch Operations")
    print("-"*40)
    
    print("\nCreating multiple leads in batch via XML-RPC:")
    batch_leads = [
        {
            'name': f"Batch Lead 1 XML-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'partner_name': 'Batch Company 1',
            'contact_name': 'Batch Contact 1',
            'email_from': 'batch1@example.com',
            'description': 'Batch lead 1 via XML-RPC'
        },
        {
            'name': f"Batch Lead 2 XML-RPC {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'partner_name': 'Batch Company 2',
            'contact_name': 'Batch Contact 2',
            'email_from': 'batch2@example.com',
            'description': 'Batch lead 2 via XML-RPC'
        }
    ]
    batch_lead_ids = api.create_leads_batch_xmlrpc(batch_leads)
    if batch_lead_ids:
        print(f"✓ Created {len(batch_lead_ids)} leads in batch: {batch_lead_ids}")
    else:
        print("✗ Failed to create leads in batch")
    
    if batch_lead_ids:
        print("\nUpdating multiple leads in batch via XML-RPC:")
        batch_updates = {
            lead_id: {'description': f'Updated batch lead {i+1} via XML-RPC'}
            for i, lead_id in enumerate(batch_lead_ids)
        }
        update_results = api.update_leads_batch_xmlrpc(batch_updates)
        success_count = sum(1 for success in update_results.values() if success)
        print(f"✓ Successfully updated {success_count} out of {len(batch_updates)} leads")
    
    # Clean up - Delete leads
    print("\n5. Cleanup - Deleting Test Leads")
    print("-"*40)
    
    all_test_leads = []
    if lead_id_xmlrpc:
        all_test_leads.append(lead_id_xmlrpc)
    if lead_id_jsonrpc:
        all_test_leads.append(lead_id_jsonrpc)
    all_test_leads.extend(batch_lead_ids)
    
    if all_test_leads:
        print(f"\nDeleting {len(all_test_leads)} test leads in batch via JSON-RPC:")
        delete_results = api.delete_leads_batch_jsonrpc(all_test_leads)
        success_count = sum(1 for success in delete_results.values() if success)
        print(f"✓ Successfully deleted {success_count} out of {len(all_test_leads)} leads")
    
    print("\n" + "="*80)
    print("DEMONSTRATION COMPLETE")
    print("="*80)


if __name__ == "__main__":
    try:
        demo_usage()
    except KeyboardInterrupt:
        print("\nDemonstration interrupted by user.")
    except Exception as e:
        print(f"\nAn error occurred during the demonstration: {str(e)}")
        logger.exception("Demonstration error")