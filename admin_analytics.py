# admin_analytics.py - FIXED VERSION
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
import numpy as np

def get_supabase_client():
    """Get Supabase client."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================
# SQL QUERY 1: Query Logs by Document Type
# ============================================
def get_queries_by_document_type():
    """Analyze queries by document type."""
    try:
        supabase = get_supabase_client()
        
        # Fetch data separately and join in Python
        queries = supabase.table("queries").select("*").execute()
        retrieval_logs = supabase.table("retrieval_logs").select("*").execute()
        documents = supabase.table("documents").select("*").execute()
        
        # Convert to DataFrames
        queries_df = pd.DataFrame(queries.data) if queries.data else pd.DataFrame()
        retrieval_df = pd.DataFrame(retrieval_logs.data) if retrieval_logs.data else pd.DataFrame()
        documents_df = pd.DataFrame(documents.data) if documents.data else pd.DataFrame()
        
        if queries_df.empty or retrieval_df.empty or documents_df.empty:
            return pd.DataFrame()
        
        # Merge dataframes
        merged = retrieval_df.merge(queries_df, left_on='query_id', right_on='id', suffixes=('_ret', '_query'))
        merged = merged.merge(documents_df, left_on='doc_id', right_on='doc_id', suffixes=('', '_doc'))
        
        # Group by document type
        result = merged.groupby('doc_type').agg({
            'id_query': 'count',
            'latency_ms': 'mean',
            'avg_similarity_score': 'mean'
        }).reset_index()
        
        result.columns = ['doc_type', 'query_count', 'avg_latency', 'avg_similarity']
        
        return result
        
    except Exception as e:
        print(f"Error in get_queries_by_document_type: {e}")
        return pd.DataFrame()
    
# ============================================
# SQL QUERY 2: Most Frequently Retrieved Files
# ============================================
def get_most_retrieved_documents():
    """Get most frequently retrieved documents - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("retrieval_logs").select("filename, doc_id, similarity_score").execute()
        
        if not result.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(result.data)
        
        grouped = df.groupby(['filename', 'doc_id']).agg({
            'similarity_score': ['count', 'mean', 'max']
        }).reset_index()
        
        grouped.columns = ['filename', 'doc_id', 'retrieval_count', 'avg_score', 'max_score']
        grouped = grouped.sort_values('retrieval_count', ascending=False).head(20)
        
        return grouped
        
    except Exception as e:
        print(f"Error in get_most_retrieved_documents: {e}")
        return pd.DataFrame()

# ============================================
# SQL QUERY 3: Average Latency by Query Length
# ============================================
def get_latency_by_query_length():
    """Analyze latency by query length - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("queries").select("query_length, latency_ms, retrieval_success").execute()
        
        if not result.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(result.data)
        
        # Create length bins
        df['length_bin'] = pd.cut(
            df['query_length'], 
            bins=[0, 20, 50, 100, 200, float('inf')],
            labels=['0-20', '21-50', '51-100', '101-200', '200+']
        )
        
        grouped = df.groupby('length_bin', observed=True).agg({
            'latency_ms': ['mean', 'median', 'std', 'count'],
            'retrieval_success': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0
        }).reset_index()
        
        grouped.columns = ['length_bin', 'avg_latency', 'median_latency', 'std_latency', 'query_count', 'success_rate']
        
        return grouped
        
    except Exception as e:
        print(f"Error in get_latency_by_query_length: {e}")
        return pd.DataFrame()

# ============================================
# SQL QUERY 4: Accuracy/Confidence Trends Over Time
# ============================================
def get_confidence_trends():
    """Get similarity score trends over time - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("queries").select(
            "created_at, avg_similarity_score, retrieval_success, latency_ms"
        ).order("created_at", desc=False).execute()
        
        if not result.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(result.data)
        
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        
        daily = df.groupby('date').agg({
            'avg_similarity_score': 'mean',
            'retrieval_success': lambda x: (x.sum() / len(x) * 100) if len(x) > 0 else 0,
            'latency_ms': 'mean'
        }).reset_index()
        
        daily.columns = ['date', 'avg_similarity', 'success_rate', 'avg_latency']
        
        return daily
        
    except Exception as e:
        print(f"Error in get_confidence_trends: {e}")
        return pd.DataFrame()

# ============================================
# SQL QUERY 5: Query Success Rate Analysis
# ============================================
def get_query_success_metrics():
    """Calculate overall query success metrics - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("queries").select(
            "retrieval_success, num_sources_retrieved, avg_similarity_score"
        ).execute()
        
        if not result.data:
            return {}
        
        df = pd.DataFrame(result.data)
        
        total_queries = len(df)
        successful = df['retrieval_success'].sum()
        failed = total_queries - successful
        
        metrics = {
            'total_queries': int(total_queries),
            'successful_queries': int(successful),
            'failed_queries': int(failed),
            'success_rate': float((successful / total_queries * 100) if total_queries > 0 else 0),
            'avg_sources_retrieved': float(df['num_sources_retrieved'].mean()),
            'avg_similarity': float(df['avg_similarity_score'].mean()),
            'queries_with_high_confidence': int(len(df[df['avg_similarity_score'] > 0.8])),
            'queries_with_low_confidence': int(len(df[df['avg_similarity_score'] < 0.5]))
        }
        
        return metrics
        
    except Exception as e:
        print(f"Error in get_query_success_metrics: {e}")
        return {}

# ============================================
# SQL QUERY 6: Embedding Similarity Distribution
# ============================================
def get_similarity_distribution():
    """Get distribution of similarity scores (cosine similarity) - ENHANCED VERSION."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.table("retrieval_logs").select(
            "similarity_score, query_id, doc_id, filename"
        ).execute()
        
        if not result.data:
            return pd.DataFrame()
        
        df = pd.DataFrame(result.data)
        
        # Add cosine similarity bins for analysis
        df['cosine_similarity'] = df['similarity_score']  # Clarify this is cosine similarity
        df['similarity_bin'] = pd.cut(
            df['cosine_similarity'],
            bins=[0, 0.3, 0.5, 0.7, 0.85, 1.0],
            labels=['Very Low (0-0.3)', 'Low (0.3-0.5)', 'Medium (0.5-0.7)', 
                    'High (0.7-0.85)', 'Very High (0.85-1.0)']
        )
        
        return df
        
    except Exception as e:
        print(f"Error in get_similarity_distribution: {e}")
        return pd.DataFrame()

def get_cosine_similarity_stats(df):
    """Calculate detailed cosine similarity statistics."""
    if df.empty:
        return {}
    
    stats = {
        'mean': df['cosine_similarity'].mean(),
        'median': df['cosine_similarity'].median(),
        'std': df['cosine_similarity'].std(),
        'min': df['cosine_similarity'].min(),
        'max': df['cosine_similarity'].max(),
        'q25': df['cosine_similarity'].quantile(0.25),
        'q75': df['cosine_similarity'].quantile(0.75),
        'very_high_count': len(df[df['cosine_similarity'] >= 0.85]),
        'high_count': len(df[(df['cosine_similarity'] >= 0.7) & (df['cosine_similarity'] < 0.85)]),
        'medium_count': len(df[(df['cosine_similarity'] >= 0.5) & (df['cosine_similarity'] < 0.7)]),
        'low_count': len(df[(df['cosine_similarity'] >= 0.3) & (df['cosine_similarity'] < 0.5)]),
        'very_low_count': len(df[df['cosine_similarity'] < 0.3])
    }
    return stats
# ============================================
# SQL QUERY 7: User Interaction Frequency
# ============================================
def get_user_interaction_stats():
    """Analyze user interaction patterns - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        # Get queries per user
        queries_result = supabase.table("queries").select("username, created_at").execute()
        queries_df = pd.DataFrame(queries_result.data) if queries_result.data else pd.DataFrame()
        
        # Get documents per user - WITHOUT created_at since it doesn't exist
        docs_result = supabase.table("documents").select("uploaded_by").execute()
        docs_df = pd.DataFrame(docs_result.data) if docs_result.data else pd.DataFrame()
        
        if queries_df.empty and docs_df.empty:
            return pd.DataFrame()
        
        # Process queries
        if not queries_df.empty:
            queries_df['created_at'] = pd.to_datetime(queries_df['created_at'])
            user_queries = queries_df.groupby('username').agg({
                'created_at': ['count', 'min', 'max']
            }).reset_index()
            user_queries.columns = ['username', 'query_count', 'first_query', 'last_query']
        else:
            user_queries = pd.DataFrame(columns=['username', 'query_count', 'first_query', 'last_query'])
        
        # Process documents - SIMPLIFIED
        if not docs_df.empty:
            user_docs = docs_df.groupby('uploaded_by').size().reset_index()
            user_docs.columns = ['username', 'docs_uploaded']
        else:
            user_docs = pd.DataFrame(columns=['username', 'docs_uploaded'])
        
        # Merge
        if not user_queries.empty and not user_docs.empty:
            user_stats = pd.merge(user_queries, user_docs, on='username', how='outer').fillna(0)
        elif not user_queries.empty:
            user_stats = user_queries.copy()
            user_stats['docs_uploaded'] = 0
        elif not user_docs.empty:
            user_stats = user_docs.copy()
            user_stats['query_count'] = 0
        else:
            return pd.DataFrame()
        
        return user_stats
        
    except Exception as e:
        print(f"Error in get_user_interaction_stats: {e}")
        return pd.DataFrame()
    
# ============================================
# SQL QUERY 8: System Error/Fallback Frequency
# ============================================
def get_error_frequency():
    """Analyze system errors and fallback patterns - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        # System logs
        logs_result = supabase.table("system_logs").select("log_type, module, created_at").execute()
        logs_df = pd.DataFrame(logs_result.data) if logs_result.data else pd.DataFrame()
        
        # Failed queries
        queries_result = supabase.table("queries").select(
            "retrieval_success, error_message, created_at"
        ).execute()
        queries_df = pd.DataFrame(queries_result.data) if queries_result.data else pd.DataFrame()
        
        error_stats = {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_module': {},
            'failed_queries': 0,
            'error_rate': 0
        }
        
        if not logs_df.empty:
            error_logs = logs_df[logs_df['log_type'] == 'error']
            error_stats['total_errors'] = len(error_logs)
            error_stats['errors_by_module'] = error_logs['module'].value_counts().to_dict()
        
        if not queries_df.empty:
            failed = queries_df[queries_df['retrieval_success'] == False]
            error_stats['failed_queries'] = len(failed)
            error_stats['error_rate'] = (len(failed) / len(queries_df) * 100) if len(queries_df) > 0 else 0
            
            # Error messages distribution
            if 'error_message' in failed.columns:
                error_messages = failed['error_message'].dropna()
                if not error_messages.empty:
                    error_stats['errors_by_type'] = error_messages.value_counts().to_dict()
        
        return error_stats
        
    except Exception as e:
        print(f"Error in get_error_frequency: {e}")
        return {
            'total_errors': 0,
            'errors_by_type': {},
            'errors_by_module': {},
            'failed_queries': 0,
            'error_rate': 0
        }

# ============================================
# EVALUATION METRICS
# ============================================
def calculate_evaluation_metrics():
    """Calculate comprehensive evaluation metrics - FIXED VERSION."""
    try:
        supabase = get_supabase_client()
        
        # Get all queries
        queries = supabase.table("queries").select("*").execute()
        
        if not queries.data:
            return {}
        
        queries_df = pd.DataFrame(queries.data)
        
        metrics = {
            # Retrieval Metrics
            'retrieval_accuracy': float((queries_df['retrieval_success'].sum() / len(queries_df) * 100)),
            'avg_sources_per_query': float(queries_df['num_sources_retrieved'].mean()),
            'avg_similarity_score': float(queries_df['avg_similarity_score'].mean()),
            
            # Performance Metrics
            'avg_latency_ms': float(queries_df['latency_ms'].mean()),
            'median_latency_ms': float(queries_df['latency_ms'].median()),
            'p95_latency_ms': float(queries_df['latency_ms'].quantile(0.95)),
            'p99_latency_ms': float(queries_df['latency_ms'].quantile(0.99)),
            
            # Quality Metrics
            'high_confidence_rate': float(len(queries_df[queries_df['avg_similarity_score'] > 0.8]) / len(queries_df) * 100),
            'low_confidence_rate': float(len(queries_df[queries_df['avg_similarity_score'] < 0.5]) / len(queries_df) * 100),
            
            # Response Metrics
            'avg_query_length': float(queries_df['query_length'].mean()),
            'avg_answer_length': float(queries_df['answer_length'].mean()),
            
            # System Health
            'total_queries': int(len(queries_df)),
            'failed_queries': int(len(queries_df[queries_df['retrieval_success'] == False])),
            'error_rate': float(len(queries_df[queries_df['retrieval_success'] == False]) / len(queries_df) * 100)
        }
        
        return metrics
        
    except Exception as e:
        print(f"Error in calculate_evaluation_metrics: {e}")
        return {}

# ============================================
# VISUALIZATION FUNCTIONS
# ============================================
def plot_queries_by_doc_type(df):
    """Plot queries by document type."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(
            x=df['doc_type'], 
            y=df['query_count'], 
            name='Query Count', 
            marker_color='lightblue',
            text=df['query_count'],
            textposition='outside'
        )
    )
    
    fig.update_layout(
        title='Query Count by Document Type',
        xaxis_title='Document Type',
        yaxis_title='Number of Queries',
        height=400,
        showlegend=False
    )
    
    return fig

def plot_latency_by_query_length(df):
    """Plot latency by query length."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['length_bin'].astype(str),
        y=df['avg_latency'],
        name='Avg Latency',
        error_y=dict(type='data', array=df['std_latency'].fillna(0)),
        text=df['query_count'],
        texttemplate='n=%{text}',
        textposition='outside',
        marker_color='skyblue'
    ))
    
    fig.update_layout(
        title='Average Latency by Query Length',
        xaxis_title='Query Length (characters)',
        yaxis_title='Latency (ms)',
        height=400
    )
    
    return fig

def plot_confidence_trends(df):
    """Plot confidence trends over time."""
    if df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Average Similarity Score Over Time', 'Success Rate Over Time'),
        vertical_spacing=0.15
    )
    
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['avg_similarity'], mode='lines+markers', name='Avg Similarity', line=dict(color='blue')),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['success_rate'], mode='lines+markers', name='Success Rate', line=dict(color='green')),
        row=2, col=1
    )
    
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Similarity Score", row=1, col=1)
    fig.update_yaxes(title_text="Success Rate (%)", row=2, col=1)
    
    fig.update_layout(height=600, showlegend=True)
    return fig

def plot_similarity_distribution(df):
    """Plot cosine similarity score distribution with enhanced analysis."""
    if df.empty:
        return None
    
    # Create subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Cosine Similarity Distribution',
            'Cosine Similarity by Bin',
            'Cosine Similarity Box Plot',
            'Cumulative Distribution'
        ),
        specs=[[{"type": "histogram"}, {"type": "bar"}],
               [{"type": "box"}, {"type": "scatter"}]]
    )
    
    # 1. Histogram
    fig.add_trace(
        go.Histogram(
            x=df['cosine_similarity'],
            nbinsx=30,
            name='Cosine Similarity',
            marker_color='lightblue',
            showlegend=False
        ),
        row=1, col=1
    )
    
    # 2. Bar chart by bins
    bin_counts = df['similarity_bin'].value_counts().sort_index()
    fig.add_trace(
        go.Bar(
            x=bin_counts.index.astype(str),
            y=bin_counts.values,
            name='Count by Bin',
            marker_color='lightcoral',
            text=bin_counts.values,
            textposition='outside',
            showlegend=False
        ),
        row=1, col=2
    )
    
    # 3. Box plot
    fig.add_trace(
        go.Box(
            y=df['cosine_similarity'],
            name='Cosine Similarity',
            marker_color='lightgreen',
            showlegend=False
        ),
        row=2, col=1
    )
    
    # 4. Cumulative distribution
    sorted_scores = np.sort(df['cosine_similarity'])
    cumulative = np.arange(1, len(sorted_scores) + 1) / len(sorted_scores) * 100
    fig.add_trace(
        go.Scatter(
            x=sorted_scores,
            y=cumulative,
            mode='lines',
            name='Cumulative %',
            line=dict(color='purple', width=2),
            showlegend=False
        ),
        row=2, col=2
    )
    
    # Update axes labels
    fig.update_xaxes(title_text="Cosine Similarity", row=1, col=1)
    fig.update_yaxes(title_text="Frequency", row=1, col=1)
    
    fig.update_xaxes(title_text="Similarity Range", row=1, col=2)
    fig.update_yaxes(title_text="Count", row=1, col=2)
    
    fig.update_yaxes(title_text="Cosine Similarity", row=2, col=1)
    
    fig.update_xaxes(title_text="Cosine Similarity", row=2, col=2)
    fig.update_yaxes(title_text="Cumulative %", row=2, col=2)
    
    fig.update_layout(
        height=800,
        showlegend=False,
        title_text="Cosine Similarity Analysis"
    )
    
    return fig

def plot_user_interactions(df):
    """Plot user interaction stats."""
    if df.empty:
        return None
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df['username'],
        y=df['query_count'],
        name='Queries',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=df['username'],
        y=df['docs_uploaded'],
        name='Documents',
        marker_color='lightcoral'
    ))
    
    fig.update_layout(
        title='User Activity Overview',
        xaxis_title='User',
        yaxis_title='Count',
        barmode='group',
        height=400
    )
    
    return fig

# ============================================
# MAIN DASHBOARD FUNCTION
# ============================================
def show_admin_dashboard():
    """Main admin dashboard."""
    st.markdown("# Admin Analytics Dashboard")
    st.markdown("---")
    
    # Refresh button
    if st.button(" Refresh Data"):
        st.rerun()
    
    # Evaluation Metrics Overview
    st.markdown("##  Evaluation Metrics Overview")
    metrics = calculate_evaluation_metrics()
    
    if metrics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Retrieval Accuracy", f"{metrics.get('retrieval_accuracy', 0):.1f}%")
            st.metric("Avg Similarity Score", f"{metrics.get('avg_similarity_score', 0):.3f}")
        
        with col2:
            st.metric("Avg Latency", f"{metrics.get('avg_latency_ms', 0):.0f}ms")
            st.metric("P95 Latency", f"{metrics.get('p95_latency_ms', 0):.0f}ms")
        
        with col3:
            st.metric("Total Queries", f"{metrics.get('total_queries', 0)}")
            st.metric("Error Rate", f"{metrics.get('error_rate', 0):.1f}%")
        
        with col4:
            st.metric("High Confidence Rate", f"{metrics.get('high_confidence_rate', 0):.1f}%")
    else:
        st.info("No data available yet. Start using the system to generate metrics!")
    
    st.markdown("---")
    
    # SQL Query Results
    tabs = st.tabs([
        "Query 1",
        "Query 2",
        "Query 3",
        "Query 4",
        "Query 5",
        "Query 6",
        "Query 7",
        "Query 8"
    ])
    
    # Tab 1: Queries by Document Type
    with tabs[0]:
        st.markdown("### SQL Query 1: Query Logs by Document Type")
        with st.spinner("Loading data..."):
            df1 = get_queries_by_document_type()
        if not df1.empty:
            st.plotly_chart(plot_queries_by_doc_type(df1), use_container_width=True)
            st.dataframe(df1, use_container_width=True)
        else:
            st.info("No data available yet. Upload documents and ask questions to generate data.")
    
    # Tab 2: Most Retrieved Documents
    with tabs[1]:
        st.markdown("### SQL Query 2: Most Frequently Retrieved Files")
        with st.spinner("Loading data..."):
            df2 = get_most_retrieved_documents()
        if not df2.empty:
            fig = px.bar(df2.head(10), x='filename', y='retrieval_count', 
                         title='Top 10 Most Retrieved Documents',
                         labels={'retrieval_count': 'Retrieval Count', 'filename': 'Document'})
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(df2, use_container_width=True)
        else:
            st.info("No data available yet")
    
    # Tab 3: Latency by Query Length
    with tabs[2]:
        st.markdown("### SQL Query 3: Average Latency by Query Length")
        with st.spinner("Loading data..."):
            df3 = get_latency_by_query_length()
        if not df3.empty:
            st.plotly_chart(plot_latency_by_query_length(df3), use_container_width=True)
            st.dataframe(df3, use_container_width=True)
        else:
            st.info("No data available yet")
    
    # Tab 4: Confidence Trends
    with tabs[3]:
        st.markdown("### SQL Query 4: Accuracy/Confidence Trends Over Time")
        with st.spinner("Loading data..."):
            df4 = get_confidence_trends()
        if not df4.empty:
            st.plotly_chart(plot_confidence_trends(df4), use_container_width=True)
            st.dataframe(df4, use_container_width=True)
        else:
            st.info("No data available yet")
    
    # Tab 5: Success Metrics
    with tabs[4]:
        st.markdown("### SQL Query 5: Query Success Rate Analysis")
        with st.spinner("Loading data..."):
            success_metrics = get_query_success_metrics()
        if success_metrics:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Queries", success_metrics.get('total_queries', 0))
                st.metric("Successful Queries", success_metrics.get('successful_queries', 0))
                st.metric("Failed Queries", success_metrics.get('failed_queries', 0))
            with col2:
                st.metric("Success Rate", f"{success_metrics.get('success_rate', 0):.1f}%")
                st.metric("Avg Sources Retrieved", f"{success_metrics.get('avg_sources_retrieved', 0):.2f}")
                st.metric("High Confidence Queries", success_metrics.get('queries_with_high_confidence', 0))
        else:
            st.info("No data available yet")
    
    # Tab 6: Similarity Distribution
    with tabs[5]:
        st.markdown("### SQL Query 6: Embedding Cosine Similarity Distribution")
        st.markdown("*Cosine similarity measures the angular distance between query and document embeddings (range: -1 to 1, higher is better)*")
        
        with st.spinner("Loading data..."):
            df6 = get_similarity_distribution()
        
        if not df6.empty:
            # Enhanced visualization
            st.plotly_chart(plot_similarity_distribution(df6), use_container_width=True)
            
            # Detailed statistics
            st.markdown("####  Cosine Similarity Statistics")
            stats = get_cosine_similarity_stats(df6)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Mean", f"{stats['mean']:.3f}")
                st.metric("Std Dev", f"{stats['std']:.3f}")
            with col2:
                st.metric("Median", f"{stats['median']:.3f}")
                st.metric("Min", f"{stats['min']:.3f}")
            with col3:
                st.metric("Q1 (25%)", f"{stats['q25']:.3f}")
                st.metric("Q3 (75%)", f"{stats['q75']:.3f}")
            with col4:
                st.metric("Max", f"{stats['max']:.3f}")
                st.metric("Total Retrievals", f"{len(df6)}")
            with col5:
                st.metric("Very High (≥0.85)", f"{stats['very_high_count']}")
                st.metric("High (0.7-0.85)", f"{stats['high_count']}")
            
            
            # Show detailed data
            st.markdown("#### Detailed Data")
            display_df = df6[['filename', 'cosine_similarity', 'similarity_bin']].sort_values(
                'cosine_similarity', ascending=False
            )
            st.dataframe(display_df, use_container_width=True)
            
        else:
            st.info("No data available yet")
    
    # Tab 7: User Activity
    with tabs[6]:
        st.markdown("### SQL Query 7: User Interaction Frequency")
        with st.spinner("Loading data..."):
            df7 = get_user_interaction_stats()
        if not df7.empty:
            st.plotly_chart(plot_user_interactions(df7), use_container_width=True)
            st.dataframe(df7, use_container_width=True)
        else:
            st.info("No data available yet")
    
    # Tab 8: Error Analysis
    with tabs[7]:
        st.markdown("### SQL Query 8: System Error/Fallback Frequency")
        with st.spinner("Loading data..."):
            error_stats = get_error_frequency()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total System Errors", error_stats.get('total_errors', 0))
        with col2:
            st.metric("Failed Queries", error_stats.get('failed_queries', 0))
        with col3:
            st.metric("Error Rate", f"{error_stats.get('error_rate', 0):.1f}%")
        
        if error_stats.get('errors_by_module'):
            st.markdown("#### Errors by Module")
            error_df = pd.DataFrame(list(error_stats['errors_by_module'].items()), 
                                    columns=['Module', 'Error Count'])
            fig = px.pie(error_df, values='Error Count', names='Module', 
                        title='Error Distribution by Module')
            st.plotly_chart(fig, use_container_width=True)