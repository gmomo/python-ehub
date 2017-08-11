#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 17:10:01 2017

@author: soumyadipghosh
"""
from pyomo.core import *
from pyomo.opt import SolverFactory, SolverManagerFactory
import pyomo.environ
import numpy as np
from bokeh.models import ColumnDataSource,HoverTool,Select,Legend,LegendItem,ColorBar,LinearColorMapper
from bkcharts import Bar
from bokeh.plotting import figure, output_file, show,curdoc
from bokeh.palettes import brewer,Viridis256,Plasma256
from bokeh.models.widgets import Panel, Tabs
from bokeh.layouts import column,row
from bokeh.models.widgets import RadioButtonGroup
from bkcharts.attributes import cat,color
from bkcharts.operations import blend
import networkx as nx

from ehub_multienergy import data,model

class VizTool:
    
    def __init__(self):
        self.n_hubs = data.numberofhubs
        self.n_forms = data.numberofdemands
        self.n_techs = len(data.Technologies[0].columns) + 1
        self.demand = data.Demands()
        self.model = model
        self.cmatrix = data.cMatrix()
        self.cap_dict = model.Capacities.get_values()
        
        max_time = 0
        for key in self.demand:
            if key[1] > max_time:
                max_time = key[1]
        self.time_steps = max_time
        self.week_h = 168
        self.time_weeks = self.time_steps // self.week_h
        
        self.nodes = []
        for hubs in range(1,self.n_hubs+1):
            self.nodes.append("Node" + str(hubs))
        
        self.e_forms = []
        for forms in range(1,self.n_forms+1):
            self.e_forms.append("Form" + str(forms))
        
        self.e_techs = []
        for techs in range(1,self.n_techs+1):
            self.e_techs.append("Tech " + str(techs))
               
              
    def demand_plot(self):
        data_dict = {}
        for forms in range(1,self.n_forms+1):
            data_dict['node_data_' + str(forms)] = np.zeros((self.time_steps+1,self.n_hubs+1))
            
        data_dict['time_step'] = np.linspace(1,self.time_steps+1,self.time_steps+1)
        
        for hub_step in range(1,self.n_hubs+1):
            for time_step in range(1,self.time_steps+1):
                for forms in range(1,self.n_forms+1):
                    (data_dict['node_data_' + str(forms)])[time_step][hub_step] = self.demand[hub_step,time_step,forms]
                    
        for forms in range(1,self.n_forms+1):
            for hub_step in range(1,self.n_hubs+1):
                data_dict['n' + str(hub_step) + str(forms)] = data_dict['node_data_' + str(forms)][1:,hub_step]
            data_dict['n' + str(forms)] = data_dict['n'+str(1)+str(forms)]
        
        for forms in range(1,self.n_forms+1):    
            data_dict['n_sum' + str(forms)] = np.sum(data_dict["node_data_" + str(forms)][1:,], axis=1)
        
        data_source = ColumnDataSource(data=data_dict)
        color = brewer['Set1'][self.n_forms]
      
        #Demand Plot 1
        demand_plot_1 = figure(plot_width=1000, plot_height=300,title="Total energy Consumption")
        demand_plot_1.xaxis.axis_label = "Hours"
        demand_plot_1.yaxis.axis_label = "Energy Consumption(kW)"
        for forms in range(1,self.n_forms+1):
            d_line = demand_plot_1.line('time_step','n_sum' + str(forms),legend = "Form " + str(forms),color=color[forms-1],source = data_source)
            demand_plot_1.add_tools(HoverTool(renderers = [d_line],tooltips=[('Hour', '@time_step'),('Value', '@n_sum' + str(forms))]))
            
        demand_plot_1.legend.location = "top_left"
        demand_plot_1.legend.click_policy="hide"
        
        #Demand Plot 2
        demand_plot_2 = figure(plot_width=1000, plot_height=300,title="Energy Consumption per Node")
        demand_plot_2.xaxis.axis_label = "Hours"
        demand_plot_2.yaxis.axis_label = "Energy Consumption(kW)"
        for forms in range(1,self.n_forms+1):
            d_line = demand_plot_2.line('time_step','n' + str(forms),source=data_source,legend = "Form " + str(forms),color=color[forms-1])
            demand_plot_2.add_tools(HoverTool(renderers = [d_line],tooltips=[('Hour', '@time_step'),('Value', '@n' + str(forms))]))
        
        demand_plot_2.legend.location = "top_left"
        demand_plot_2.legend.click_policy="hide"
        
        def update_plot(attrname, old, new):
            node = node_select.value[-1:]
            for forms in range(1,self.n_forms+1):
                data_source.data['n' + str(forms)] = data_source.data['n' + str(node) + str(forms)]
                   
        node_select = Select(value="Node1", title='Nodes', options=self.nodes)    
        node_select.on_change('value', update_plot)
        
        return column(demand_plot_1,row(demand_plot_2,node_select))
    
    def production(self):

        prodmat = {}
    
        for hub_step in range(1,self.n_hubs+1):
            for time_step in range(1,self.time_steps+1):
                for forms in range(1,self.n_forms+1):
                    for techs in range(1,self.n_techs+1):
                        prodmat[(hub_step,time_step,forms,techs)] = self.demand[(hub_step,time_step,forms)]*self.cmatrix[(techs,forms)]
    
        prod_data = {}
    
        for hub_step in range(1,self.n_hubs+1):
            for forms in range(1,self.n_forms+1):
                for techs in range(1,self.n_techs+1):
                    prod_data['n' + str(hub_step) + str(forms) + str(techs)] = np.zeros((self.time_steps+1))
                    for time_step in range(1,self.time_steps+1):
                        prod_data['n' + str(hub_step) + str(forms) + str(techs)][time_step] = prodmat[(hub_step,time_step,forms,techs)]
    
        prod_data['time_step'] = np.linspace(1,self.time_steps+1,self.time_steps+1)
        
        cols = []
        for techs in range(1,self.n_techs+1):
            cols.append('n' + str(11) + str(techs))
    
        bar = Bar(prod_data,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Energy Production per Node for Each Form of Energy",
                  color=color(columns='medal',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="Energy Production(kW)")
    
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"),
            ]
        )
    
        bar.add_tools(hover)
        
        tech_legend1 = self.create_legend()
    
        prod_dataw = {}
        if(self.time_weeks == 0):
            for k,v in prod_data.items():
                prod_dataw[k] = np.zeros((1))
            prod_dataw['time_step'] = np.zeros((1))
        else:
            for k,v in prod_data.items():
                v = v[:self.time_weeks * self.week_h]
                prod_dataw[k] = np.sum(v.reshape(-1, self.week_h), axis=1)
            prod_dataw['time_step'] = np.linspace(1,self.time_weeks,self.time_weeks)
    
        bar_w = Bar(prod_dataw,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Energy Production per Node for Each Form of Energy per Week",
                  color=color(columns='medal',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Weeks",
                  ylabel="Energy Production(kW)")
    
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"),
            ]
        )
    
        bar_w.add_tools(hover)
    
        def update_plot(attrname, old, new):
            node = node_select.value[-1:]
            form = form_select.value[-1:]
    
            cols = []
    
            for techs in range(1,self.n_techs+1):
                cols.append('n' + str(node) + str(form) + str(techs))    
    
            pbar = Bar(prod_data,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Energy Production per Node for Each Form of Energy",
                  color=color(columns='medal',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="Energy Production(kW)")
    
            hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"),
            ]
        )
            pbar.add_tools(hover)
    
            disp_row.children[0] = pbar
    
        def update_plotw(attrname, old, new):
            node = node_selectw.value[-1:]
            form = form_selectw.value[-1:]
    
            cols = []
    
            for techs in range(1,self.n_techs+1):
                cols.append('n' + str(node) + str(form) + str(techs))
                print ('n' + str(node) + str(form) + str(techs))
    
    
            pbarw = Bar(prod_dataw,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Energy Production per Node for Each Form of Energy",
                  color=color(columns='medal',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Weeks",
                  ylabel="Energy Production(kW)")
    
            hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"),
            ]
        )
            pbarw.add_tools(hover)
    
            disp_row_2.children[0] = pbarw
            fin_column.children[1] = self.create_legend()
            
        
        node_select = Select(value="Node1", title='Nodes', options=self.nodes)
        form_select = Select(value="Form1", title='Forms', options=self.e_forms)
    
        node_select.on_change('value', update_plot)
        form_select.on_change('value', update_plot)
    
        controls = column(node_select, form_select)
        disp_row = row(bar,controls)
    
        node_selectw = Select(value="Node1", title='Nodes', options=self.nodes)
        form_selectw = Select(value="Form1", title='Forms', options=self.e_forms)
    
        node_selectw.on_change('value', update_plotw)
        form_selectw.on_change('value', update_plotw)
    
        controlsw = column(node_selectw, form_selectw)
        disp_row_2 = row(bar_w,controlsw)
        
        fin_column = column(disp_row,tech_legend1,disp_row_2)
        
        return fin_column
               
    def capacities(self):
    
        cap_source = {}
        
        for techs in range(1,self.n_techs+1):
            for forms in range(1,self.n_forms+1):
                cap_source['n' + str(techs) + str(forms)] = np.zeros((self.n_hubs))
                for hub_step in range(1,self.n_hubs+1):
                    cap_source['n' + str(techs) + str(forms)][hub_step-1] = self.cap_dict[(hub_step,techs,forms)]
                #cap_source['n' + str(techs) + str(forms)] = np.array(cap_source['n' + str(techs) + str(forms)])
        
        for forms in range(1,self.n_forms+1):
            cap_source['n' + str(self.n_techs+2) + str(forms)] = np.zeros((self.n_hubs))
            for hub_step in range(1,self.n_hubs+1):
                for techs in range(1,self.n_techs+1):
                    cap_source['n' + str(self.n_techs+2) + str(forms)][hub_step-1] += cap_source['n' + str(techs) + str(forms)][hub_step-1]
        
        cap_source['n_list'] = []
        for hub_step in range(1,self.n_hubs+1):
            cap_source['n_list'].append( "Node " + str(hub_step))
        cap_source['n_list'] = np.array(cap_source['n_list'])
        #cap_source['n21'] = np.array([34.8,78,54,12,90])
        
        cols = []
        for techs in range(1,self.n_techs+1):
            cols.append('n' + str(1) + str(techs))
        
        v_bar = Bar(cap_source,
                  values=blend(*cols,name ="medal_v",labels_name = "medals"),
                  label='n_list',
                  stack='medals',
                  legend=None,
                  color=color(columns='medals',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  title="Energy Capacity per Node for Each Technology",
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Nodes",
                  ylabel="Energy Capacity(kW)")
        
        hover = HoverTool(
            tooltips = [
                ("Node", "@n_list"),
                ("Value", "@height"), 
            ]
        )
        
        v_bar.add_tools(hover)
        
        def update_plot(attrname, old, new):
            form = form_select.value[-1:]
            cols = []
            for techs in range(1,self.n_techs+1):
                cols.append('n' + str(techs) + str(form))
                
            tbar = Bar(cap_source,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='n_list',
                  stack='medal',
                  legend=None,
                  color=color(columns='medal',
                             palette=brewer['Set1'][self.n_techs],
                             sort=True),
                  title="Energy Capacity per Node for Each Form of Energy",
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Nodes",
                  ylabel="Storage Capacity(kW)")
        
            hover = HoverTool(
            tooltips = [
                ("Node", "@n_list"),
                ("Value", "@height"), 
            ]
        )
            tbar.add_tools(hover)
            
            disp_row_1.children[0] = tbar
            fin_column.children[1] = self.create_legend()
        
        form_select = Select(value="Form1", title='Forms', options=self.e_forms)    
        form_select.on_change('value', update_plot)
        
        tech_legend1 = self.create_legend() 
        
        storage = model.StorageCap.get_values()
        storage_dict = {}
        storage_dict['n_list'] = np.array(cap_source['n_list'])
           
        for forms in range(1,self.n_forms+1):
            storage_dict['f' + str(forms)] = np.zeros((self.n_hubs))
            for hub_step in range(1,self.n_hubs+1):
                storage_dict['f' + str(forms)][hub_step-1] = storage[(hub_step,forms)]
        
        storage_dict['f1'] = [23,67,98,41,11]
        
        storage_bar = Bar(storage_dict,
                  values='f1',
                  label='n_list',
                  legend=None,
                  title="Storage Capacity per Node",
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Nodes",
                  ylabel="Storage Capacity(kW)")
        
        hover = HoverTool(
            tooltips = [
                ("Node", "@n_list"),
                ("Value", "@height"), 
            ]
        )
        
        def update_plot_st(attrname, old, new):
            form = form_select_st.value[-1:]
            
            st_bar = Bar(storage_dict,
                  values='f' + str(form),
                  label='n_list',
                  legend=None,
                  title="Storage Capacity per Node",
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Nodes",
                  ylabel="Storage Capacity(kW)")
        
            hover = HoverTool(
            tooltips = [
                ("Node", "@n_list"),
                ("Value", "@height"), 
            ]
        )
            
            st_bar.add_tools(hover)
            
            disp_row_2.children[0] = st_bar
            fin_column.children[1] = self.create_legend()
        
        form_select_st = Select(value="Form1", title='Forms', options=self.e_forms)    
        form_select_st.on_change('value', update_plot_st)
        
        gis_dict = {}
        gis_dict['x'] = 14*np.random.rand(self.n_hubs,)
        gis_dict['y'] = 6*np.random.rand(self.n_hubs,)
        x_range = (gis_dict['x'].min(), gis_dict['x'].max())
        y_range = (gis_dict['y'].min(), gis_dict['y'].max())
        gis_plot = figure(title="Node Locations with Capacities",plot_width=600, plot_height=600,x_range=x_range,y_range=y_range)
        gis_plot.xaxis.axis_label = "X Coordinates"
        gis_plot.yaxis.axis_label = "Y Coordinates"
        
        for k,v in cap_source.items():
            gis_dict[k] = v
            if(k != 'n_list' and v.max(axis=0)!= 0):
                gis_dict[k + 'n'] = v/v.max(axis=0)*abs(max(y_range)*3)
            else:
                gis_dict[k + 'n'] = gis_dict[k]
        
        gis_dict['temp'] = gis_dict['n11']
        gis_dict['tempn'] = gis_dict['n11n']
                
        gis_source = ColumnDataSource(data=gis_dict)
        
        gis_plot.circle(x='x',
                        y='y',
                        radius='tempn',
                        source=gis_source,
                        radius_dimension='y',
                        radius_units='screen',
                        )
        
        gis_hover = HoverTool(tooltips = [
                                ("X", "@x"),
                                ("Y", "@y"),
                                ("Value","@temp")
                                ]
                        )
        
        gis_plot.add_tools(gis_hover)
        
        def update_plot_gis(attrname, old, new):
            form = form_select_gis.value[-1:]
            tech = tech_select_gis.value[-1:]
            
            gis_source.data['temp'] = gis_source.data['n' + str(tech) +str(form)]
            gis_source.data['tempn'] = gis_source.data['n' + str(tech) +str(form) + 'n']
        
        form_select_gis = Select(value="Form1", title='Forms', options=self.e_forms)
        tech_select_gis = Select(value="Tech1", title='Technologies', options=self.e_techs)
        form_select_gis.on_change('value', update_plot_gis)
        tech_select_gis.on_change('value', update_plot_gis)
        
        controls = column(form_select)
        controls_2 = column(form_select_st)
        controls_3 = column(form_select_gis,tech_select_gis)
        disp_row_1 = row(v_bar,controls)
        disp_row_2 = row(storage_bar,controls_2)
        disp_row_3 = row(gis_plot,controls_3)
        
        fin_column = column(disp_row_1,tech_legend1,disp_row_2,disp_row_3)
        
        return fin_column
          
    def networks(self):
        
        transfer_source = model.DH_Q.get_values()
        demand = data.Demands()
        n_hubs = data.numberofhubs
        n_forms = data.numberofdemands
        
        max_time = 0
        for key in demand:
            if(key[1] > max_time):
                max_time = key[1]
        time_steps = max_time
        
        t_dict = {}            
        for forms in range(1,n_forms+1):
            for node_i in range(1,n_hubs+1):
                for node_j in range(1,n_hubs+1):
                    t_dict[(node_i,node_j,forms)] = 0
                    for timestep in range(1,time_steps):
                        t_dict[(node_i,node_j,forms)]+=transfer_source[(node_i,node_j,timestep,forms)]
                    
        for k,v in t_dict.items():
            t_dict[k] = 500*np.random.rand()
            
        for forms in range(1,n_forms+1):
            for node_i in range(1,n_hubs+1):
                for node_j in range(node_i,n_hubs+1):
                    if(t_dict[node_i,node_j,forms] > t_dict[node_j,node_i,forms]):
                        t_dict[node_i,node_j,forms] -= t_dict[node_j,node_i,forms]
                        t_dict.pop((node_j,node_i,forms), None)
                    else:
                        t_dict[node_j,node_i,forms] -= t_dict[node_i,node_j,forms]
                        t_dict.pop((node_i,node_j,forms), None)
                        
        x_coord_1 = 14*np.random.rand(n_hubs,)
        y_coord_1 = 6*np.random.rand(n_hubs,)
        
        trans_dict_1 = {}
        trans_dict_1['x'] = x_coord_1
        trans_dict_1['y'] = y_coord_1
        
        nodes = []
        for hubs in range(1,n_hubs+1):
            nodes.append("Node" + str(hubs))
            
        trans_dict_1['node_list'] = nodes
        
        for forms in range(1,n_forms+1):
            trans_dict_1['xf' + str(forms)] = []
            trans_dict_1['yf' + str(forms)] = []
            trans_dict_1['valuesf' + str(forms)] = []
            for k,v in t_dict.items():
                if(v !=0 and k[2] == forms ):
                    trans_dict_1['xf' + str(forms)].append([x_coord_1[k[0]-1],x_coord_1[k[1]-1]])
                    trans_dict_1['yf' + str(forms)].append([y_coord_1[k[0]-1],y_coord_1[k[1]-1]])
                    trans_dict_1['valuesf' + str(forms)].append(v)
                    
        
        trans_dict_1['valuesdummy'] = trans_dict_1['valuesf1']
        trans_dict_1['xdummy'] = trans_dict_1['xf1']
        trans_dict_1['ydummy'] = trans_dict_1['yf1']
        
        x_range = (min(x_coord_1),max(x_coord_1))
        y_range = (min(y_coord_1), max(y_coord_1))
        
        key_max = max(t_dict.keys(), key=(lambda k: t_dict[k]))
        key_min = min(t_dict.keys(), key=(lambda k: t_dict[k]))
        
        lcm = LinearColorMapper(palette=Plasma256, low=t_dict[key_min], high=t_dict[key_max])
        color_bar = ColorBar(color_mapper=lcm, location=(0, 0))
        line_dict_1_cds = ColumnDataSource(data = trans_dict_1)
        
        transfer_plot_1 = figure(title="Network Plot",plot_width=600, plot_height=600,x_range=x_range,y_range=y_range,toolbar_location="above")
        lines = transfer_plot_1.multi_line(xs='xdummy', ys='ydummy',color={'field': 'valuesdummy', 'transform': lcm},line_width = 3 ,line_join='miter',source=line_dict_1_cds)
        circles = transfer_plot_1.circle(x='x',y='y',radius=5,fill_alpha=0.9,source=line_dict_1_cds,radius_dimension='y',radius_units='screen')
        
        transfer_plot_1.add_tools(HoverTool(renderers = [lines],tooltips=[('Value', '@valuesdummy')]))
        transfer_plot_1.add_tools(HoverTool(renderers = [circles],tooltips=[('Node', '@node_list')]))
        
        def update_plot_networks(attrname, old, new):
            form = form_select_network.value[-1:]
            line_dict_1_cds.data['valuesdummy'] = line_dict_1_cds.data['valuesf' + str(form)]
            line_dict_1_cds.data['xdummy'] = line_dict_1_cds.data['xf' + str(form)]
            line_dict_1_cds.data['ydummy'] = line_dict_1_cds.data['yf' + str(form)]
            
        e_forms = []
        for forms in range(1,n_forms+1):
            e_forms.append("Form" + str(forms))
        
        form_select_network = Select(value="Form1", title='Forms', options=e_forms)    
        form_select_network.on_change('value', update_plot_networks)
        
        transfer_plot_1.add_layout(color_bar, 'right')
        
        G = nx.DiGraph()
        G.add_nodes_from(np.linspace(1,n_hubs,n_hubs))
        
        edges = {}
        
        for forms in range(1,n_forms+1):
            edges["e" + str(forms)] = []
            for k,v in t_dict.items():
                if(k[2] == forms):
                    edges["e" + str(forms)].append((k[0],k[1],v))
        
        coords = {}
        
        for forms in range(1,n_forms+1):
            G.add_weighted_edges_from(edges["e" + str(forms)])
            coords["pos" + str(forms)] = nx.spring_layout(G,scale=20,weight=None,iterations=50)
            G.remove_edges_from(edges["e" + str(forms)])
        
        x_coords = {}
        y_coords = {}
        
        for forms in range(1,n_forms+1):
            x_coords["f" + str(forms)] = []
            for hubs in range(1,n_hubs+1):
                x_coords["f" + str(forms)].append(coords["pos" + str(forms)][hubs][0])
                
        for forms in range(1,n_forms+1):
            y_coords["f" + str(forms)] = []
            for hubs in range(1,n_hubs+1):
                y_coords["f" + str(forms)].append(coords["pos" + str(forms)][hubs][1])
                
        trans_dict = {}
        
        for k,v in x_coords.items():
            trans_dict["xc" + k] = v
        for k,v in y_coords.items():
            trans_dict["yc" + k] = v
        
        nodes = []
        for hubs in range(1,n_hubs+1):
            nodes.append("Node" + str(hubs))
            
        trans_dict['node_list'] = nodes
        
        for forms in range(1,n_forms+1):
            trans_dict['xf' + str(forms)] = []
            trans_dict['yf' + str(forms)] = []
            trans_dict['valuesf' + str(forms)] = []
            for k,v in t_dict.items():
                if(v !=0 and k[2] == forms ):
                    trans_dict['xf' + str(forms)].append([x_coords["f" + str(forms)][k[0]-1],x_coords["f" + str(forms)][k[1]-1]])
                    trans_dict['yf' + str(forms)].append([y_coords["f" + str(forms)][k[0]-1],y_coords["f" + str(forms)][k[1]-1]])
                    trans_dict['valuesf' + str(forms)].append(v)
                    
        
        trans_dict['valuesdummy'] = trans_dict['valuesf1']
        trans_dict['xdummy'] = trans_dict['xf1']
        trans_dict['ydummy'] = trans_dict['yf1']
        trans_dict['xcdummy'] = trans_dict["xcf1"]
        trans_dict['ycdummy'] = trans_dict["ycf1"]
        
        x_range = (0,20)
        y_range = (0, 20)
        
        key_max = max(t_dict.keys(), key=(lambda k: t_dict[k]))
        key_min = min(t_dict.keys(), key=(lambda k: t_dict[k]))
        
        lcm = LinearColorMapper(palette=Plasma256, low=t_dict[key_min], high=t_dict[key_max])
        color_bar = ColorBar(color_mapper=lcm, location=(0, 0))
        line_dict_cds = ColumnDataSource(data = trans_dict)
        
        transfer_plot = figure(title="Force Directed Plot",plot_width=600, plot_height=600,x_range=x_range,y_range=y_range,toolbar_location="above")
        lines = transfer_plot.multi_line(xs='xdummy', ys='ydummy',color={'field': 'valuesdummy', 'transform': lcm},line_width = 3 ,line_join='miter',source=line_dict_cds)
        circles = transfer_plot.circle(x='xcdummy',y='ycdummy',radius=5,fill_alpha=0.9,source=line_dict_cds,radius_dimension='y',radius_units='screen')
        
        transfer_plot.add_tools(HoverTool(renderers = [lines],tooltips=[('Value', '@valuesdummy')]))
        transfer_plot.add_tools(HoverTool(renderers = [circles],tooltips=[('Node', '@node_list')]))
        
        def update_plot_force(attrname, old, new):
            form = form_select_st.value[-1:]
            line_dict_cds.data['valuesdummy'] = line_dict_cds.data['valuesf' + str(form)]
            line_dict_cds.data['xdummy'] = line_dict_cds.data['xf' + str(form)]
            line_dict_cds.data['ydummy'] = line_dict_cds.data['yf' + str(form)]
            line_dict_cds.data['xcdummy'] = line_dict_cds.data['xcf' + str(form)]
            line_dict_cds.data['ycdummy'] = line_dict_cds.data['ycf' + str(form)]
        
        
        e_forms = []
        for forms in range(1,n_forms+1):
            e_forms.append("Form" + str(forms))
        
        form_select_st = Select(value="Form1", title='Forms', options=e_forms)    
        form_select_st.on_change('value', update_plot_force)
        
        transfer_plot.add_layout(color_bar, 'right')
        
        #output_file("Networks.html", title="networks example")
        return column(row(transfer_plot_1,form_select_network),row(transfer_plot,form_select_st))
        
        #show(transfer_plot)
    
    def costs(self):
    
        op_cost = model.OpCost.get_values()[None]
        opcost_dict = {}
        opcost_dict.update((x, y*op_cost) for x, y in model.P.get_values().items())
        opcost_data = {}
        
        for techs in range(1,self.n_techs+1):
            opcost_data['t' + str(techs)] = np.zeros((self.time_steps))
            for time_step in range(1,self.time_steps):
                for hub_step in range(1,self.n_hubs+1):
                    opcost_data['t' + str(techs)][time_step] += opcost_dict[(hub_step,time_step,techs)]
                    
        opcost_data['time_step'] = np.linspace(1,self.time_steps,self.time_steps)
        
        cols = []
        for techs in range(1,self.n_techs+1):
            cols.append('t' + str(techs))
        
        opcost_bar = Bar(opcost_data,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Operational Cost per form of Technology",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_techs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="CHF")
        
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        opcost_bar.add_tools(hover)
        
        tech_legend1 = self.create_legend()
        
        opcost_dataw = {}
        if(self.time_weeks == 0):
            for k,v in opcost_data.items():
                opcost_dataw[k] = np.zeros((1))
            opcost_dataw['time_step'] = np.zeros((1))
        else:
            for k,v in opcost_data.items():
                v = v[:self.time_weeks * self.week_h]
                print (v[:self.time_weeks * self.week_h])
                opcost_dataw[k] = np.sum(v.reshape(-1, self.week_h), axis=1)
            opcost_dataw['time_step'] = np.linspace(1,self.time_weeks,self.time_weeks)
        
        opcostbar_w = Bar(opcost_dataw,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Operational Cost per form of Technology per Week",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_techs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="CHF")
        
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        mtc_cost = data.VarMaintCost()
        
        P = model.P.get_values()
        
        for hub_step in range(1,self.n_hubs+1):
            for techs in range(1,self.n_techs+1):
                for time_step in range(1,self.time_steps):
                    P[(hub_step,time_step,techs)] *= mtc_cost[(hub_step,techs)]
        
        mtccost_data = {}        
        for techs in range(1,self.n_techs+1):
            mtccost_data['t' + str(techs)] = np.zeros((self.time_steps))
            for time_step in range(1,self.time_steps):
                for hub_step in range(1,self.n_hubs+1):
                    mtccost_data['t' + str(techs)][time_step] += P[(hub_step,time_step,techs)]
        
        mtccost_data['time_step'] = np.linspace(1,self.time_steps,self.time_steps)
        
        mtccost_bar = Bar(mtccost_data,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Maintenance Cost per form of Technology",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_techs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="CHF")
        
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        mtccost_bar.add_tools(hover)
        
        opc = model.OpCost.get_values()[None]
        mtc = model.MaintCost.get_values()[None]
        inc = model.InvCost.get_values()[None]
        income = model.IncomeExp.get_values()[None]
        
        sum_pi = opc + mtc + inc + income
        values = [opc,mtc,inc,income]
        percents = [0,opc/sum_pi,(opc+mtc)/sum_pi,(opc+mtc+inc)/sum_pi,(opc+mtc+inc+income)/sum_pi]
        
        starts = [p*2*np.pi for p in percents[:-1]]
        ends = [p*2*np.pi for p in percents[1:]]
        colors = brewer["Set1"][4]
        
        cost_labels = ["Operational Cost","Maintenance Cost","Investment Cost","Income"]
        
        pie_chart_source = ColumnDataSource(
            data=dict(
                x=[0 for x in percents],
                y=[0 for x in percents],
                percents=percents,
                starts=starts,
                colors=colors,
                ends=ends,
                values=values,
                cost_labels = cost_labels
            )
        )
        
        pie_chart = figure(title="Cost vs Income Breakdown",plot_width = 500,plot_height=300,toolbar_location="left")
        r = pie_chart.wedge(source = pie_chart_source,x='x', y='y',alpha=0.8, radius=0.8, start_angle='starts' , end_angle='ends', color='colors')
        legend = Legend(items=[LegendItem(label=dict(field="cost_labels"), renderers=[r])], location=(0,-50)) 
        pie_chart.add_layout(legend, 'right') 
        
        hover = HoverTool(
            tooltips = [
                ("Type", "@cost_labels"),
                ("Value", "@values"), 
            ]
        )
    
        pie_chart.add_tools(hover)
        pie_chart.xaxis.visible = False
        pie_chart.xgrid.visible = False
        pie_chart.yaxis.visible = False
        pie_chart.ygrid.visible = False

        op_column = column(opcost_bar,tech_legend1,opcostbar_w,mtccost_bar,pie_chart)
        return op_column
    
    def carbon_emissions(self):
        
        c_em_tech = {} 
        c_em_tech['time_step'] = np.linspace(1,self.time_steps,self.time_steps)
        for techs in range(1,self.n_techs+1):
            c_em_tech['t' + str(techs)] = np.zeros((self.time_steps))
            for time_step in range(1,self.time_steps):
                c_em_tech['t' + str(techs)][time_step] = value(model.carbonFactors[techs] * sum(model.P[i, time_step,techs] for i in model.hub_i))
        
        cols = []
        for techs in range(1,self.n_techs+1):
            cols.append('t' + str(techs))
        
        bar = Bar(c_em_tech,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Carbon Emissions per form of Technology",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_techs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Hours",
                  ylabel="Carbon Emissions(kg)")
        
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        bar.add_tools(hover)
        
        tech_legend1 = self.create_legend()
        
        c_em_techw = {}
        if(self.time_weeks == 0):
            for k,v in c_em_tech.items():
                c_em_techw[k] = np.zeros((1))
            c_em_techw['time_step'] = np.zeros((1))
        else:
            for k,v in c_em_tech.items():
                v = v[:self.time_weeks * self.week_h]
                c_em_techw[k] = np.sum(v.reshape(-1, self.week_h), axis=1)
            c_em_techw['time_step'] = np.linspace(1,self.time_weeks,self.time_weeks)
        
        bar_w = Bar(c_em_techw,
                  values=blend(*cols, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Carbon Emissions per form of Technology per Week",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_techs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Weeks",
                  ylabel="Carbon Emissions(kg)")
        
        hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        c_em_nodes = {} 
        c_em_nodes['time_step'] = np.linspace(1,self.time_steps,self.time_steps)
        
        for hub_step in range(1,self.n_hubs+1):    
            c_em_nodes['n' + str(hub_step)] = np.zeros((self.time_steps))
            for time_step in range(1,self.time_steps):
                c_em_nodes['n' + str(hub_step)][time_step] = value(sum(model.carbonFactors[inp] * model.P[hub_step, time_step,inp] for inp in model.In))
        
        col_nodes = []
        for hubs in range(1,self.n_hubs+1):
            col_nodes.append('n' + str(hubs))
        
        n_bar = Bar(c_em_nodes,
                  values=blend(*col_nodes, name='medals', labels_name='medal'),
                  label='time_step',
                  stack='medal',
                  legend=None,
                  title="Carbon Emissions per Node",
                  color=color(columns='medal',
                              palette=brewer['Set1'][self.n_hubs],
                              sort=True),
                  plot_width = 1000,
                  plot_height = 300,
                  xlabel="Nodes",
                  ylabel="Carbon Emissions(kg)")
        
        n_hover = HoverTool(
            tooltips = [
                ("Hour", "@time_step"),
                ("Value", "@height"), 
            ]
        )
        
        n_bar.add_tools(n_hover)
        
        y = [0] * len(self.nodes)
        x = self.nodes
        #pal = ['SaddleBrown', 'Silver', 'Goldenrod']
        node_legend = figure(width = 1000,height = 50, toolbar_location=None,active_drag=None,x_range=self.nodes)
        node_legend.rect(x, y, color= brewer['Set1'][self.n_hubs], width=1, height=10)
        node_legend.yaxis.major_label_text_color = None
        node_legend.yaxis.major_tick_line_color = None
        node_legend.yaxis.minor_tick_line_color = None
        
        return column(bar,tech_legend1,bar_w,n_bar,node_legend)
    
    def exports(self):
        export = model.Pexport.get_values()
        exp_dict = {}
        
        for forms in range(1,self.n_forms+1):
            exp_dict['f' + str(forms)] = np.zeros((self.time_steps+1))
            for time_step in range(1,self.time_steps+1):
                for hub_step in range(1,self.n_hubs+1):
                    exp_dict['f' + str(forms)][time_step] += export[(hub_step,time_step,forms)]
        exp_dict['time_step'] = np.linspace(1,self.time_steps,self.time_steps)
        exp_source = ColumnDataSource(data=exp_dict)
        color = brewer['Set1'][self.n_forms]
        
        export_plot_1 = figure(plot_width=1000, plot_height=300,title="Total Energy Exported")
        export_plot_1.xaxis.axis_label = "Hours"
        export_plot_1.yaxis.axis_label = "Energy Exported(kW)"
        for forms in range(1,self.n_forms+1):
            d_line = export_plot_1.line('time_step','f' + str(forms),legend = "Form " + str(forms),color=color[forms-1],source = exp_source)
            export_plot_1.add_tools(HoverTool(renderers = [d_line],tooltips=[('Hour', '@time_step'),('Value', '@f' + str(forms))]))    
        export_plot_1.legend.location = "top_left"
        export_plot_1.legend.click_policy="hide"
                
        return column(export_plot_1)
    
    def create_legend(self):
            y = [0] * len(self.e_techs)
            x = self.e_techs
            #pal = ['SaddleBrown', 'Silver', 'Goldenrod']
            p = figure(width = 1000,height = 50, toolbar_location=None,active_drag=None,x_range=self.e_techs)
            p.rect(x, y, color= brewer['Set1'][self.n_techs], width=1, height=10)
            p.yaxis.major_label_text_color = None
            p.yaxis.major_tick_line_color = None
            p.yaxis.minor_tick_line_color = None
            return p
    
    def layout(self):
        
        self.demand_glyph = self.demand_plot()
        self.production_glyph = self.production()
        self.capacities_glyph = self.capacities()
        self.costs_glyph = self.costs()
        self.carbon_glyph = self.carbon_emissions()
        self.exports_glyph = self.exports()
        self.networks_glyph = self.networks()
        
        self.tab1 = Panel(child=self.demand_glyph, title="Energy Demand")
        self.tab2 = Panel(child=self.production_glyph, title="Energy Production")
        self.tab3 = Panel(child=self.capacities_glyph,title="Energy Capacities")
        self.tab4 = Panel(child=self.networks_glyph,title="Energy Networks")
        self.tab5 = Panel(child=self.costs_glyph,title="Energy Costs")
        self.tab6 = Panel(child=self.carbon_glyph,title="Carbon Emissions")
        self.tab7 = Panel(child = self.exports_glyph,title="Energy Exports")
        self.tabs = Tabs(tabs=[self.tab1,self.tab2,self.tab3,self.tab4,self.tab5,self.tab6,self.tab7 ])
        
        return self.tabs
        
viz = VizTool()
curdoc().add_root(viz.layout())
        
        

        
        
        

        
        


            
            
                
                            
