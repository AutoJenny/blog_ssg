import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Slider } from '@/components/ui/slider';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

// Load schema from config file
import llmSchema from '@/config/llm_schema.yaml';

interface LLMConfiguratorProps {
  action: string;
  onConfigChange: (config: any) => void;
}

export const LLMConfigurator: React.FC<LLMConfiguratorProps> = ({ action, onConfigChange }) => {
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('');

  // Create form schema based on action parameters
  const formSchema = z.object({
    model: z.string().min(1, "Model selection is required"),
    temperature: z.number().min(0).max(2),
    max_tokens: z.number().min(1).max(4096),
    top_p: z.number().min(0).max(1),
    frequency_penalty: z.number().min(-2).max(2),
    presence_penalty: z.number().min(-2).max(2),
  });

  const form = useForm({
    resolver: zodResolver(formSchema),
    defaultValues: {
      model: "",
      temperature: 0.7,
      max_tokens: 1000,
      top_p: 1.0,
      frequency_penalty: 0.0,
      presence_penalty: 0.0,
    },
  });

  useEffect(() => {
    // Load available models based on action requirements
    const actionConfig = llmSchema.actions[action];
    if (!actionConfig) return;

    const models = Object.entries(llmSchema.providers)
      .flatMap(([provider, config]) => 
        config.models
          .filter(model => 
            actionConfig.required_capabilities.every(cap => 
              model.capabilities.includes(cap)
            )
          )
          .map(model => ({
            provider,
            name: model.name,
          }))
      );

    setAvailableModels(models);
  }, [action]);

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider);
    form.setValue('model', '');
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>LLM Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onConfigChange)} className="space-y-4">
          <div className="space-y-2">
            <Label>Provider</Label>
            <Select onValueChange={handleProviderChange}>
              <SelectTrigger>
                <SelectValue placeholder="Select provider" />
              </SelectTrigger>
              <SelectContent>
                {Object.keys(llmSchema.providers).map(provider => (
                  <SelectItem key={provider} value={provider}>
                    {llmSchema.providers[provider].name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedProvider && (
            <div className="space-y-2">
              <Label>Model</Label>
              <Select onValueChange={(value) => form.setValue('model', value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select model" />
                </SelectTrigger>
                <SelectContent>
                  {availableModels
                    .filter(model => model.provider === selectedProvider)
                    .map(model => (
                      <SelectItem key={model.name} value={model.name}>
                        {model.name}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
          )}

          <div className="space-y-2">
            <Label>Temperature</Label>
            <Slider
              min={0}
              max={2}
              step={0.1}
              value={[form.watch('temperature')]}
              onValueChange={([value]) => form.setValue('temperature', value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input
              type="number"
              min={1}
              max={4096}
              {...form.register('max_tokens', { valueAsNumber: true })}
            />
          </div>

          <div className="space-y-2">
            <Label>Top P</Label>
            <Slider
              min={0}
              max={1}
              step={0.1}
              value={[form.watch('top_p')]}
              onValueChange={([value]) => form.setValue('top_p', value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Frequency Penalty</Label>
            <Slider
              min={-2}
              max={2}
              step={0.1}
              value={[form.watch('frequency_penalty')]}
              onValueChange={([value]) => form.setValue('frequency_penalty', value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Presence Penalty</Label>
            <Slider
              min={-2}
              max={2}
              step={0.1}
              value={[form.watch('presence_penalty')]}
              onValueChange={([value]) => form.setValue('presence_penalty', value)}
            />
          </div>

          <Button type="submit">Save Configuration</Button>
        </form>
      </CardContent>
    </Card>
  );
}; 