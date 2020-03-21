import numpy as np
import tensorflow as tf
import Nn
from Algorithms.tf2algos.base.policy import Policy


class MADDPG(Policy):
    '''
    Multi-Agent Deep Deterministic Policy Gradient, https://arxiv.org/abs/1706.02275
    '''
    def __init__(self,
                 s_dim,
                 a_dim_or_list,
                 is_continuous,

                 ployak=0.995,
                 actor_lr=5.0e-4,
                 critic_lr=1.0e-3,
                 share_visual_net=True,
                 n=1,
                 i=0,
                 hidden_units={
                     'actor': [32, 32],
                     'q': [32, 32]
                 },
                 **kwargs):
        assert is_continuous, 'maddpg only support continuous action space'
        raise Exception('MA系列存在问题，还未修复')
        super().__init__(
            s_dim=s_dim,
            visual_sources=0,
            visual_resolution=0,
            a_dim_or_list=a_dim_or_list,
            is_continuous=is_continuous,
            **kwargs)
        self.n = n
        self.i = i
        self.ployak = ployak

        self.share_visual_net = share_visual_net
        if self.share_visual_net:
            self.actor_visual_net = self.critic_visual_net = self._visual_net()
        else:
            self.actor_visual_net = self._visual_net()
            self.critic_visual_net = self._visual_net()
        rnn_net = self._rnn_net(self.actor_visual_net.hdim)

        # self.action_noise = Nn.NormalActionNoise(mu=np.zeros(self.a_counts), sigma=1 * np.ones(self.a_counts))
        self.action_noise = Nn.OrnsteinUhlenbeckActionNoise(mu=np.zeros(self.a_counts), sigma=0.2 * np.exp(-self.episode / 10) * np.ones(self.a_counts))

        self.actor_net = Nn.VisualObsRNN(
            net=Nn.actor_dpg(rnn_net.hdim, 0, self.a_counts, hidden_units['actor']),
            visual_net=self.actor_visual_net,
            rnn_net=rnn_net,
            rnn_net_grad=False
        )
        self.actor_target_net = Nn.VisualObsRNN(
            net=Nn.actor_dpg(rnn_net.hdim, 0, self.a_counts, hidden_units['actor']),
            visual_net=self.actor_visual_net,
            rnn_net=rnn_net,
            rnn_net_grad=False
        )
        self.q_net = Nn.VisualObsRNN(
            net=Nn.critic_q_one((rnn_net.hdim) * self.n, 0, (self.a_counts) * self.n, hidden_units['q']),
            visual_net=self.critic_visual_net,
            rnn_net=rnn_net
        )
        self.q_target_net = Nn.VisualObsRNN(
            net=Nn.critic_q_one((rnn_net.hdim) * self.n, 0, (self.a_counts) * self.n, hidden_units['q']),
            visual_net=self.critic_visual_net,
            rnn_net=rnn_net
        )
        self.update_target_net_weights(
            self.actor_target_net.uv + self.q_target_net.uv,
            self.actor_net.uv + self.q_net.uv
        )
        self.actor_lr = tf.keras.optimizers.schedules.PolynomialDecay(actor_lr, self.max_episode, 1e-10, power=1.0)
        self.critic_lr = tf.keras.optimizers.schedules.PolynomialDecay(critic_lr, self.max_episode, 1e-10, power=1.0)
        self.optimizer_critic = tf.keras.optimizers.Adam(learning_rate=self.critic_lr(self.episode))
        self.optimizer_actor = tf.keras.optimizers.Adam(learning_rate=self.actor_lr(self.episode))

        self.model_recorder(dict(
            actor=self.actor_net,
            q=self.q_net,
            optimizer_critic=self.optimizer_critic,
            optimizer_actor=self.optimizer_actor
        ))
        self.recorder.logger.info(self.action_noise)

    def show_logo(self):
        self.recorder.logger.info('''
　　ｘｘｘｘ　　　　ｘｘｘ　　　　　　　　　ｘｘ　　　　　　　　　ｘｘｘｘｘｘｘ　　　　　　　　ｘｘｘｘｘｘｘ　　　　　　　　ｘｘｘｘｘｘｘｘ　　　　　　　　ｘｘｘｘｘｘ　　　　　
　　　ｘｘｘ　　　　ｘｘ　　　　　　　　　ｘｘｘ　　　　　　　　　　　ｘ　　ｘｘｘ　　　　　　　　　ｘ　　ｘｘｘ　　　　　　　　　ｘｘ　　ｘｘ　　　　　　　ｘｘｘ　　ｘｘ　　　　　
　　　　ｘｘｘ　　ｘｘｘ　　　　　　　　　ｘｘｘ　　　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘｘ　　　　　　ｘｘ　　　　ｘ　　　　　
　　　　ｘｘｘ　　ｘｘｘ　　　　　　　　　ｘ　ｘｘ　　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘｘ　　　　　　ｘｘ　　　　　　　　　　
　　　　ｘｘｘｘ　ｘ　ｘ　　　　　　　　ｘｘ　ｘｘ　　　　　　　　　　ｘ　　　ｘｘｘ　　　　　　　　ｘ　　　ｘｘｘ　　　　　　　　ｘｘｘｘｘｘ　　　　　　　ｘ　　　ｘｘｘｘｘ　　　
　　　　ｘ　ｘｘｘｘ　ｘ　　　　　　　　ｘｘｘｘｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　　　　　　　　　　ｘｘ　　　ｘｘｘ　　　　
　　　　ｘ　ｘｘｘ　　ｘ　　　　　　　ｘｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　ｘｘ　　　　　　　　　ｘ　　　　　　　　　　　　ｘｘ　　　　ｘ　　　　　
　　　　ｘ　　ｘｘ　　ｘ　　　　　　　ｘｘ　　　ｘｘ　　　　　　　　　ｘ　　ｘｘｘ　　　　　　　　　ｘ　　ｘｘｘ　　　　　　　　　ｘ　　　　　　　　　　　　ｘｘｘ　　ｘｘ　　　　　
　　ｘｘｘｘ　ｘｘｘｘｘｘ　　　　　ｘｘｘ　　ｘｘｘｘｘ　　　　　ｘｘｘｘｘｘｘ　　　　　　　　ｘｘｘｘｘｘｘ　　　　　　　　ｘｘｘｘｘ　　　　　　　　　　　ｘｘｘｘｘｘ　　　　　
　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　　ｘｘ　　　
        ''')

    def choose_action(self, s, evaluation=False):
        return self._get_action(s, evaluation).numpy()

    def get_target_action(self, s):
        return self._get_target_action(s).numpy()

    @tf.function
    def _get_action(self, vector_input, evaluation):
        vector_input = self.cast(vector_input)
        with tf.device(self.device):
            mu = self.actor_net.choose(vector_input, None)
            if evaluation == True:
                return mu
            else:
                return tf.clip_by_value(mu + self.action_noise(), -1, 1)

    @tf.function
    def _get_target_action(self, vector_input):
        vector_input = self.cast(vector_input)
        with tf.device(self.device):
            target_mu = self.actor_target_net(vector_input, None)
        return tf.clip_by_value(target_mu + self.action_noise(), -1, 1)

    def learn(self, episode, ap, al, ss, ss_, aa, aa_, s, r):
        self.episode = episode
        ap, al, ss, ss_, aa, aa_, s, r = map(self.data_convert, (ap, al, ss, ss_, aa, aa_, s, r))
        summaries = self.train(ap, al, ss, ss_, aa, aa_, s, r)
        self.update_target_net_weights(
            self.actor_target_net.uv + self.q_target_net.uv,
            self.actor_net.uv + self.q_net.uv,
            self.ployak)
        summaries.update(dict([
            ['LEARNING_RATE/actor_lr', self.actor_lr(self.episode)],
            ['LEARNING_RATE/critic_lr', self.critic_lr(self.episode)]
        ]))
        self.write_training_summaries(self.global_step, summaries)

    def get_max_episode(self):
        """
        get the max episode of this training model.
        """
        return self.max_episode

    @tf.function(experimental_relax_shapes=True)
    def train(self, q_actor_a_previous, q_actor_a_later, ss, ss_, aa, aa_, s, r):
        with tf.device(self.device):
            with tf.GradientTape() as tape:
                q = self.q_net(ss, None, aa)
                q_target = self.q_target_net(ss_, None, aa_)
                dc_r = tf.stop_gradient(r + self.gamma * q_target)
                td_error = q - dc_r
                q_loss = 0.5 * tf.reduce_mean(tf.square(td_error))
            q_grads = tape.gradient(q_loss, self.q_net.tv)
            self.optimizer_critic.apply_gradients(
                zip(q_grads, self.q_net.tv)
            )
            with tf.GradientTape() as tape:
                mu = self.actor_net(s, None)
                mumu = tf.concat((q_actor_a_previous, mu, q_actor_a_later), axis=-1)
                q_actor = self.q_net(ss, None, mumu)
                actor_loss = -tf.reduce_mean(q_actor)
            actor_grads = tape.gradient(actor_loss, self.actor_net.tv)
            self.optimizer_actor.apply_gradients(
                zip(actor_grads, self.actor_net.tv)
            )
            self.global_step.assign_add(1)
            return dict([
                ['LOSS/actor_loss', actor_loss],
                ['LOSS/critic_loss', q_loss]
            ])

    @tf.function(experimental_relax_shapes=True)
    def train_persistent(self, q_actor_a_previous, q_actor_a_later, ss, ss_, aa, aa_, s, r):
        with tf.device(self.device):
            with tf.GradientTape(persistent=True) as tape:
                q = self.q_net(ss, None, aa)
                q_target = self.q_target_net(ss_, None, aa_)
                dc_r = tf.stop_gradient(r + self.gamma * q_target)
                td_error = q - dc_r
                q_loss = 0.5 * tf.reduce_mean(tf.square(td_error))
                mu = self.actor_net(s, None)
                mumu = tf.concat((q_actor_a_previous, mu, q_actor_a_later), axis=-1)
                q_actor = self.q_net(ss, None, mumu)
                actor_loss = -tf.reduce_mean(q_actor)
            q_grads = tape.gradient(q_loss, self.q_net.tv)
            self.optimizer_critic.apply_gradients(
                zip(q_grads, self.q_net.tv)
            )
            actor_grads = tape.gradient(actor_loss, self.actor_net.tv)
            self.optimizer_actor.apply_gradients(
                zip(actor_grads, self.actor_net.tv)
            )
            self.global_step.assign_add(1)
            return dict([
                ['LOSS/actor_loss', actor_loss],
                ['LOSS/critic_loss', q_loss]
            ])
