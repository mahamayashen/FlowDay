import { Check, CircleNotch } from '@phosphor-icons/react'
import './AgentPipelineIndicator.css'

/**
 * Visualizes the 6-agent pipeline: 4 Group A agents run in parallel,
 * then Pattern Detector → Narrative Writer → Judge run sequentially.
 */

export type AgentStatus = 'pending' | 'running' | 'done'

export interface AgentState {
  name: string
  label: string
  status: AgentStatus
}

interface AgentPipelineIndicatorProps {
  groupA: AgentState[]    // 4 agents, parallel
  groupBCD: AgentState[]  // pattern → narrative → judge, sequential
}

function AgentChip({ agent }: { agent: AgentState }): React.JSX.Element {
  return (
    <div className={`agent-chip agent-chip--${agent.status}`}>
      <div className="agent-chip-icon">
        {agent.status === 'done' && <Check size={10} weight="bold" />}
        {agent.status === 'running' && <CircleNotch size={10} className="spin" />}
      </div>
      <span className="agent-chip-label">{agent.label}</span>
    </div>
  )
}

function AgentPipelineIndicator({ groupA, groupBCD }: AgentPipelineIndicatorProps): React.JSX.Element {
  return (
    <div className="agent-pipeline" data-testid="agent-pipeline">
      <div className="agent-pipeline-section">
        <div className="agent-pipeline-label">
          <span>GROUP A</span>
          <span className="agent-pipeline-sublabel">parallel · asyncio.gather</span>
        </div>
        <div className="agent-pipeline-parallel">
          {groupA.map((a) => (
            <AgentChip key={a.name} agent={a} />
          ))}
        </div>
      </div>

      <div className="agent-pipeline-arrow">→</div>

      <div className="agent-pipeline-section">
        <div className="agent-pipeline-label">
          <span>GROUP B → C → D</span>
          <span className="agent-pipeline-sublabel">sequential</span>
        </div>
        <div className="agent-pipeline-sequential">
          {groupBCD.map((a, idx) => (
            <div key={a.name} className="agent-pipeline-seq-item">
              <AgentChip agent={a} />
              {idx < groupBCD.length - 1 && <span className="agent-pipeline-seq-arrow">→</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AgentPipelineIndicator
