import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { createBrowserRouter, redirect, RouterProvider } from 'react-router-dom';
import Routes from './configuration/routes/RouteList';
import './style.css';
import Base from './pages/Base';
import About from './pages/About';
import Channels from './pages/Channels';
import ErrorPage from './pages/ErrorPage';
import Home from './pages/Home';
import Playlist from './pages/Playlist';
import Playlists from './pages/Playlists';
import Search from './pages/Search';
import SettingsDashboard from './pages/SettingsDashboard';
import Video from './pages/Video';
import Login from './pages/Login';
import SettingsActions from './pages/SettingsActions';
import SettingsApplication from './pages/SettingsApplication';
import SettingsScheduling from './pages/SettingsScheduling';
import SettingsUser from './pages/SettingsUser';
import loadUserMeConfig from './api/loader/loadUserConfig';
import loadAuth from './api/loader/loadAuth';
import ChannelBase from './pages/ChannelBase';
import ChannelVideo from './pages/ChannelVideo';
import ChannelPlaylist from './pages/ChannelPlaylist';
import ChannelAbout from './pages/ChannelAbout';
import Download from './pages/Download';

const router = createBrowserRouter(
  [
    {
      path: Routes.Home,
      loader: async () => {
        console.log('------------ after reload');

        const auth = await loadAuth();
        if (auth.status === 403) {
          return redirect(Routes.Login);
        }

        const authData = await auth.json();

        const userConfig = await loadUserMeConfig();

        return { userConfig, auth: authData };
      },
      element: <Base />,
      errorElement: <ErrorPage />,
      children: [
        {
          index: true,
          element: <Home />,
        },
        {
          path: Routes.Video(':videoId'),
          element: <Video />,
        },
        {
          path: Routes.Channels,
          element: <Channels />,
        },
        {
          path: Routes.Channel(':channelId'),
          element: <ChannelBase />,
          children: [
            {
              index: true,
              path: Routes.ChannelVideo(':channelId'),
              element: <ChannelVideo videoType="videos" />,
            },
            {
              path: Routes.ChannelStream(':channelId'),
              element: <ChannelVideo videoType="streams" />,
            },
            {
              path: Routes.ChannelShorts(':channelId'),
              element: <ChannelVideo videoType="shorts" />,
            },
            {
              path: Routes.ChannelPlaylist(':channelId'),
              element: <ChannelPlaylist />,
            },
            {
              path: Routes.ChannelAbout(':channelId'),
              element: <ChannelAbout />,
            },
          ],
        },
        {
          path: Routes.Playlists,
          element: <Playlists />,
        },
        {
          path: Routes.Playlist(':playlistId'),
          element: <Playlist />,
        },
        {
          path: Routes.Downloads,
          element: <Download />,
        },
        {
          path: Routes.Search,
          element: <Search />,
        },
        {
          path: Routes.SettingsDashboard,
          element: <SettingsDashboard />,
        },
        {
          path: Routes.SettingsActions,
          element: <SettingsActions />,
        },
        {
          path: Routes.SettingsApplication,
          element: <SettingsApplication />,
        },
        {
          path: Routes.SettingsScheduling,
          element: <SettingsScheduling />,
        },
        {
          path: Routes.SettingsUser,
          element: <SettingsUser />,
        },
        {
          path: Routes.About,
          element: <About />,
        },
      ],
    },
    {
      path: Routes.Login,
      element: <Login />,
      errorElement: <ErrorPage />,
    },
  ],
  { basename: import.meta.env.BASE_URL },
);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
);
